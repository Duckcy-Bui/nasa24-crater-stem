"""S3-16: đóng gói mã, báo cáo và bundle từ một commit, không lấy working tree."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPORT_NAME = "BaoCao_Nhom2_NASA24"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_output(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE)


def extract_archive(raw: bytes, destination: Path) -> None:
    """Chỉ nhận thư mục và file thường, giữ byte của git archive."""
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        members = archive.getmembers()
        for member in members:
            name = PurePosixPath(member.name)
            if (name.is_absolute() or ".." in name.parts or "\\" in member.name
                    or ":" in member.name or not (member.isdir() or member.isfile())):
                raise ValueError(f"Thành phần archive không hợp lệ: {member.name}")
        destination.mkdir()
        for member in members:
            target = destination / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
                target.chmod(member.mode & 0o777)


def inventory(directory: Path) -> dict:
    result = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Không nhận symlink trong gói: {path.name}")
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = {
                "bytes": path.stat().st_size, "sha256": sha256(path),
            }
    return result


def check_zip(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
    if bad is not None:
        raise ValueError(f"ZIP hỏng: {bad}")


def verify_bundle(source: Path) -> dict:
    directory = source / "data/s106_bundle"
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    info = manifest["archive"]
    if Path(info["filename"]).name != info["filename"] or "\\" in info["filename"]:
        raise ValueError("Tên bundle không hợp lệ")
    path = directory / info["filename"]
    if path.stat().st_size != info["bytes"] or sha256(path) != info["sha256"]:
        raise ValueError("Bundle khác SHA-256/kích thước đã chốt")
    check_zip(path)
    with zipfile.ZipFile(path) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())) or set(archive.namelist()) != set(manifest["files"]):
            raise ValueError("Danh sách file bundle không khớp manifest")
        for name, expected in manifest["files"].items():
            payload = archive.read(name)
            if len(payload) != expected["bytes"] or hashlib.sha256(payload).hexdigest() != expected["sha256"]:
                raise ValueError(f"File trong bundle khác hash: {name}")
    return {"path": "ma_nguon/" + path.relative_to(source).as_posix(),
            "sha256": info["sha256"], "files_verified": len(manifest["files"])}


def validate_reports(directory: Path) -> list[Path]:
    docx = directory / f"{REPORT_NAME}.docx"
    pdf = directory / f"{REPORT_NAME}.pdf"
    if not docx.is_file() or not pdf.is_file():
        raise ValueError("Phải dựng được cả DOCX và PDF; xem build_report.log")
    check_zip(docx)
    with zipfile.ZipFile(docx) as archive:
        if not {"[Content_Types].xml", "word/document.xml"}.issubset(archive.namelist()):
            raise ValueError("DOCX thiếu nội dung Word")
    raw = pdf.read_bytes()
    if not raw.startswith(b"%PDF-") or b"%%EOF" not in raw[-1024:]:
        raise ValueError("PDF không hợp lệ hoặc chưa ghi xong")
    return [docx, pdf]


def verify_payload(directory: Path) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    actual = inventory(directory)
    actual.pop("manifest.json")
    if actual != manifest["files"]:
        raise ValueError("Nội dung gói không khớp manifest SHA-256")
    return manifest


def pending_markers(source: Path) -> dict:
    result = {}
    for path in sorted((source / "docs/bao_cao").glob("[0-9][0-9]_*.md")):
        text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
        result[path.name] = len(re.findall(r"\[CHỜ[^\]]*\]", text))
    return result


def package_commit(repo: Path, commit: str, output: Path, report_python: str = sys.executable) -> dict:
    # Giữ symlink của venv; tên lệnh đơn vẫn được tìm qua PATH.
    report_python = os.fspath(report_python)
    if os.path.dirname(report_python):
        report_python = os.path.abspath(report_python)
    repo, output = repo.resolve(), output.resolve()
    if output.exists():
        raise FileExistsError(f"Thư mục đầu ra đã tồn tại, không ghi đè: {output}")
    revision = git_output(repo, "rev-parse", "--verify", "--end-of-options", commit + "^{commit}").decode().strip()
    tree = git_output(repo, "rev-parse", revision + "^{tree}").decode().strip()
    raw = git_output(repo, "archive", "--format=tar", revision)
    output.mkdir(parents=True)
    directory = output / ("NASA24_Nhom2_" + revision[:12])
    directory.mkdir()
    source = directory / "ma_nguon"
    extract_archive(raw, source)
    for name in ["README.md", "requirements-test.txt", "scripts/build_report.py"]:
        if not (source / name).is_file():
            raise ValueError(f"Commit thiếu đầu vào đóng gói: {name}")
    source_before = inventory(source)
    bundle = verify_bundle(source)

    build = output / "report_build"
    build.mkdir()
    command = [str(report_python), "-X", "utf8", "-B", str(source / "scripts/build_report.py"), "--out", str(build)]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "MPLBACKEND": "Agg"}
    with (output / "build_report.log").open("w", encoding="utf-8") as log:
        subprocess.run(command, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    reports = validate_reports(build)
    if inventory(source) != source_before:
        raise ValueError("Nguồn từ git archive bị thay đổi trong lúc dựng báo cáo")
    report_directory = directory / "bao_cao"
    report_directory.mkdir()
    for path in reports:
        shutil.copyfile(path, report_directory / path.name)

    guide = f"""# Gói bàn giao NASA 24 · Nhóm 2

Mã nguồn và nguồn báo cáo lấy bằng git archive từ commit `{revision}`.
DOCX/PDF trong `bao_cao/` được dựng bằng script của chính commit đó.
Script đóng gói đang dùng được nhận diện riêng bằng SHA-256 trong manifest.

## Chạy trên máy nhận

Từ `ma_nguon/`, dùng Python 3.12 theo README:

```bash
python3.12 -B -m venv .venv
source .venv/bin/activate
python -B -m pip install -r requirements-test.txt
python -X utf8 -B scripts/install_s106_dataset.py
python -X utf8 -B -m streamlit run app.py --server.address 127.0.0.1
```

Windows: gọi `.venv\\Scripts\\python.exe` theo README của mã nguồn.
Bundle ngoại tuyến ở `ma_nguon/data/s106_bundle/`, không cần `data/processed/` từ máy đóng gói.
Hướng dẫn kiểm, tái tạo bảng và dựng báo cáo: `ma_nguon/README.md`,
`ma_nguon/docs/S3-10_TAI_TAO_KET_QUA.md`, `ma_nguon/docs/bao_cao/README.md`.

`manifest.json` lưu SHA-256/kích thước mọi file, trừ chính manifest.
ZIP có checksum riêng; kiểm CRC bằng `ZipFile.testzip()` rồi giải nén và kiểm từng hash.

## Phạm vi

Gói này gồm mã, bundle, hướng dẫn và bản báo cáo dựng từ commit đã chọn.
Slide, video và xác nhận thành viên chưa được nhận làm đầu vào của script.
Các dấu chờ trong báo cáo được đếm trong manifest; dựng thành công không phải nghiệm thu nội dung.
Khảo sát ít nhất 10 học sinh chưa thực hiện theo quyết định 31/10/2026.
Trưởng nhóm chốt đầu ra và bổ sung nơi nộp, hạn, tên tệp, biểu mẫu từ đề gốc.
"""
    (directory / "HUONG_DAN_BAN_GIAO.md").write_text(guide, encoding="utf-8")
    manifest = {
        "schema_version": "s316-package-1", "status": "complete",
        "scope": "Mã, báo cáo, hướng dẫn và bundle; chưa nghiệm thu bộ nộp cuối.",
        "source_commit": revision, "source_tree": tree,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "packager_sha256": sha256(Path(__file__)), "source_files": len(source_before),
        "report_build_script_sha256": source_before["scripts/build_report.py"]["sha256"],
        "report_pending_markers": pending_markers(source),
        "external_deliverables_not_checked": ["slide", "video", "xác nhận thành viên"],
        "dataset_bundle": bundle, "files": inventory(directory),
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verify_payload(directory)

    archive_path = output / (directory.name + ".zip")
    partial = output / (directory.name + ".zip.part")
    expected_files = inventory(directory)
    with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in expected_files:
            archive.write(directory / name, directory.name + "/" + name)
    check_zip(partial)
    with zipfile.ZipFile(partial) as archive:
        expected_names = {directory.name + "/" + name for name in expected_files}
        if len(archive.namelist()) != len(expected_names) or set(archive.namelist()) != expected_names:
            raise ValueError("ZIP thiếu/thừa file so với gói đã kiểm")
        for name, expected in expected_files.items():
            raw = archive.read(directory.name + "/" + name)
            if len(raw) != expected["bytes"] or hashlib.sha256(raw).hexdigest() != expected["sha256"]:
                raise ValueError(f"ZIP khác manifest: {name}")
    partial.rename(archive_path)
    archive_hash = sha256(archive_path)
    archive_path.with_suffix(".zip.sha256").write_text(f"{archive_hash}  {archive_path.name}\n", encoding="utf-8")
    result = {"source_commit": revision, "package": directory.name, "zip": archive_path.name,
              "zip_sha256": archive_hash, "payload_files": len(manifest["files"]),
              "source_files": len(source_before), "zip_crc": "pass", "payload_sha256": "pass"}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True, help="Commit đã chốt; không lấy file chưa commit")
    parser.add_argument("--output", type=Path, required=True, help="Thư mục mới, không ghi đè")
    parser.add_argument("--report-python", default=sys.executable, help="Python đã cài requirements-report.txt")
    args = parser.parse_args(argv)
    try:
        result = package_commit(ROOT, args.commit, args.output, args.report_python)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, tarfile.TarError, zipfile.BadZipFile) as error:
        print(f"Đóng gói thất bại: {error}", file=sys.stderr)
        return 1
    print(f"Complete: {args.output / result['zip']}")
    print(f"SHA-256: {result['zip_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
