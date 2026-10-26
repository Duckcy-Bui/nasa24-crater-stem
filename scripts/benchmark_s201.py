"""S2-01: same-machine NumPy baseline/current timing, without library evaluation.

python -B scripts/benchmark_s201.py --images moon_ap16_m106777343r_c01
The baseline source is loaded from this repository's explicit Git commit.
Only Hough is timed; preprocessing, I/O and rendering are excluded.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
import types
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.hough import detect_circles, resolve_hough_params
from src.pipeline import load_image, radius_range
from src.preprocessing import preprocess

BASELINE_REF = 'eb8278cc82901cc28dbbc6509b0ff0b6bfefa0cc'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def baseline_source(ref):
    commit = subprocess.run(
        ['git', 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}'],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    source = subprocess.run(['git', 'show', commit + ':src/hough.py'],
                            cwd=ROOT, capture_output=True, check=True).stdout
    module = types.ModuleType('s201_baseline')
    exec(compile(source, '<baseline:' + commit + '>', 'exec'), module.__dict__)
    return commit, source, module.detect_circles


def measure(edges, theta, lo, hi, params, baseline, repeats, warmups):
    """Alternate order; compare every complete output, including integer votes."""
    functions = {'baseline': baseline, 'optimized': detect_circles}
    results = {}
    for name, function in functions.items():
        for _ in range(warmups):
            function(edges, lo, hi, params, theta=theta)
        results[name] = {'seconds': [], 'stable': True, 'circles': None}
    identical = True
    for repetition in range(repeats):
        order = ('baseline', 'optimized') if repetition % 2 == 0 else ('optimized', 'baseline')
        for name in order:
            start = time.perf_counter()
            circles = functions[name](edges, lo, hi, params, theta=theta)
            seconds = time.perf_counter() - start
            row = results[name]
            row['seconds'].append(seconds)
            if row['circles'] is not None:
                row['stable'] &= row['circles'] == circles
            row['circles'] = circles
        identical &= results['baseline']['circles'] == results['optimized']['circles']
    for row in results.values():
        values = row['seconds']
        row.update(median_seconds=float(np.median(values)), min_seconds=min(values),
                   max_seconds=max(values), circle_count=len(row['circles']),
                   hit_max_circles=len(row['circles']) >= params['max_circles'])
    return {'results': results, 'identical_outputs': identical,
            'speedup': results['baseline']['median_seconds'] / results['optimized']['median_seconds']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images', nargs='+', default=['moon_ap16_m106777343r_c01'])
    parser.add_argument('--processed-dir', type=Path, default=ROOT/'data/processed')
    parser.add_argument('--config', type=Path, default=ROOT/'configs/s201_hough.json')
    parser.add_argument('--baseline-ref', default=BASELINE_REF)
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--warmups', type=int, default=1)
    parser.add_argument('--output-root', type=Path, default=ROOT/'outputs/s201')
    args = parser.parse_args(argv)
    if args.repeats < 3 or args.warmups < 1:
        parser.error('Use repeats >= 3 and warmups >= 1.')
    if len(set(args.images)) != len(args.images):
        parser.error('Image IDs must be unique.')
    if any(Path(name).name != name or '/' in name or '\\' in name for name in args.images):
        parser.error('Use image IDs, not file paths.')
    try:
        params = resolve_hough_params(json.loads(args.config.read_text(encoding='utf-8')))
        commit, source, baseline = baseline_source(args.baseline_ref)
    except (OSError, ValueError, TypeError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
    run_id = 's201_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '_' + uuid4().hex[:8]
    directory = args.output_root/run_id
    directory.mkdir(parents=True, exist_ok=False)
    (directory/'baseline_hough.py').write_bytes(source)
    (directory/'config.json').write_text(json.dumps({'hough': params}, indent=2)+'\n', encoding='utf-8')
    paths = ['src/hough.py', 'src/preprocessing.py', 'src/pipeline.py', 'scripts/benchmark_s201.py']
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True)
    status = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True, check=True)
    report = {'task': 'S2-01', 'created_at_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Hough only; identical cached edges/theta/config/radius grid; no I/O or rendering',
              'baseline_commit': commit, 'baseline_sha256': hashlib.sha256(source).hexdigest(),
              'current_commit': head.stdout.strip(), 'git_status': status.stdout,
              'source_sha256': {p: digest(ROOT/p) for p in paths},
              'environment': {'python': platform.python_version(), 'numpy': np.__version__,
                              'platform': platform.platform(), 'cpu': platform.processor()},
              'params': params, 'repeats': args.repeats, 'warmups': args.warmups,
              'image_ids': args.images, 'images': [], 'status': 'running',
              'limits': ['No accuracy claim: real labels are sparse/unreviewed.',
                         'Timing samples are local measurements, not performance guarantees.',
                         'No S2-05 deduplication or S2-06 library comparison.']}

    def save_report():
        (directory/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2,
                                                       allow_nan=False)+'\n', encoding='utf-8')
    save_report()
    try:
        for image_id in args.images:
            metadata, image, valid = load_image(image_id, args.processed_dir)
            start = time.perf_counter()
            pre = preprocess(image, metadata, None, valid_mask=valid)
            seconds_preprocess = time.perf_counter() - start
            lo, hi = radius_range(metadata, params)
            radii = list(range(lo, hi+1, params['radius_step_px']))
            case = measure(pre['edges'], pre['theta'], lo, hi, params, baseline,
                           args.repeats, args.warmups)
            mask_path = args.processed_dir/(image_id+'_valid_mask.npy')
            case.update(image_id=image_id, data_kind=metadata['data_kind'], metadata=metadata,
                        preprocessing=pre['params'], seconds_preprocess_single=seconds_preprocess,
                        edge_count=int(pre['edges'].sum()), searched_radii_px=radii,
                        image_sha256=digest(args.processed_dir/(image_id+'.npy')),
                        metadata_sha256=digest(args.processed_dir/(image_id+'.json')),
                        valid_mask_sha256=digest(mask_path) if mask_path.exists() else None)
            np.savez_compressed(directory/(image_id+'_inputs.npz'),
                                edges=pre['edges'], theta=pre['theta'], gray=pre['gray'],
                                valid_mask=pre['valid_mask'])
            report['images'].append(case)
            save_report()
            print(f"{image_id}: {case['speedup']:.2f}x; identical={case['identical_outputs']}", flush=True)
        report['status'] = 'passed' if all(
            case['identical_outputs'] and all(row['stable'] for row in case['results'].values())
            for case in report['images']) else 'failed'
    except Exception as error:
        report.update(status='error', error=f'{type(error).__name__}: {error}')
        save_report()
        raise
    save_report()
    fields = ['image_id', 'edge_count', 'radius_min', 'radius_last', 'radius_step', 'radius_count',
              'method', 'circles', 'hit_max_circles', 'median_seconds', 'min_seconds', 'max_seconds',
              'speedup', 'identical_outputs']
    with (directory/'timings.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for case in report['images']:
            radii = case['searched_radii_px']
            for name, row in case['results'].items():
                writer.writerow(dict(image_id=case['image_id'], edge_count=case['edge_count'],
                                     radius_min=radii[0], radius_last=radii[-1],
                                     radius_step=params['radius_step_px'], radius_count=len(radii),
                                     method=name, circles=row['circle_count'],
                                     hit_max_circles=row['hit_max_circles'],
                                     median_seconds=row['median_seconds'], min_seconds=row['min_seconds'],
                                     max_seconds=row['max_seconds'], speedup=case['speedup'],
                                     identical_outputs=case['identical_outputs']))
    print('Saved:', directory, flush=True)
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
