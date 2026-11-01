"""Commit isolation and failure controls; no processed dataset or real report tools."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import venv
import zipfile

from scripts import package_s316 as packager

COMMIT = "a" * 40
BUILDER = '''from pathlib import Path
import argparse
import zipfile
parser = argparse.ArgumentParser()
parser.add_argument("--out", type=Path)
out = parser.parse_args().out
text = (Path(__file__).resolve().parents[1] / "README.md").read_text()
with zipfile.ZipFile(out / "BaoCao_Nhom2_NASA24.docx", "w") as z:
    z.writestr("[Content_Types].xml", "<Types/>")
    z.writestr("word/document.xml", "<document>" + text + "</document>")
PDF_LINE
'''


def snapshot(*, missing_pdf=False, bad_bundle=False, failed_build=False, expected_prefix=None):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("crop.fixture", b"tiny bundle fixture")
    bundle = buffer.getvalue()
    manifest = {"archive": {"filename": "bundle.zip", "bytes": len(bundle),
                            "sha256": "wrong" if bad_bundle else hashlib.sha256(bundle).hexdigest()},
                "files": {"crop.fixture": {"bytes": 19, "sha256": hashlib.sha256(b"tiny bundle fixture").hexdigest()}}}
    pdf_line = "pass" if missing_pdf else '(out / "BaoCao_Nhom2_NASA24.pdf").write_bytes(b"%PDF-1.4\\n" + text.encode() + b"\\n%%EOF\\n")'
    builder = "raise SystemExit(9)\n" if failed_build else BUILDER.replace("PDF_LINE", pdf_line)
    if expected_prefix is not None:
        builder = ("import sys\nfrom pathlib import Path\n"
                   f"assert Path(sys.prefix) == Path({str(expected_prefix)!r})\n" + builder)
    files = {"README.md": b"committed snapshot", "requirements-test.txt": b"",
             "scripts/build_report.py": builder.encode(), "docs/bao_cao/01_test.md": b"[CH\xe1\xbb\x9c test]",
             "data/s106_bundle/manifest.json": json.dumps(manifest).encode(),
             "data/s106_bundle/bundle.zip": bundle}
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as archive:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(data), 0o644
            archive.addfile(info, io.BytesIO(data))
    return raw.getvalue()


def git_fixture(raw):
    def read(repo, *args):
        if args == ("archive", "--format=tar", COMMIT):
            return raw
        if args == ("rev-parse", COMMIT + "^{tree}"):
            return ("b" * 40 + "\n").encode()
        if args == ("rev-parse", "--verify", "--end-of-options", "selected^{commit}"):
            return (COMMIT + "\n").encode()
        raise AssertionError(args)
    return read


class PackageTests(unittest.TestCase):
    def build(self, root, report_python=sys.executable, **options):
        repo = root / "live"
        repo.mkdir(exist_ok=True)
        (repo / "README.md").write_text("uncommitted working tree")
        (repo / "scripts").mkdir(exist_ok=True)
        (repo / "scripts/build_report.py").write_text("raise SystemExit('wrong source')")
        with patch.object(packager, "git_output", side_effect=git_fixture(snapshot(**options))):
            return packager.package_commit(repo, "selected", root / "output", report_python)

    def make_report_python(self, caller):
        directory = caller / "report_env"
        venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt").create(directory)
        executable = directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        return directory, executable

    def test_relative_report_python_uses_caller_directory_and_keeps_venv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            caller = root / "caller"
            directory, executable = self.make_report_python(caller)
            with contextlib.chdir(caller):
                try:
                    result = self.build(root, report_python=os.path.relpath(executable, caller),
                                        expected_prefix=directory)
                except (OSError, subprocess.CalledProcessError) as error:
                    self.fail(f"Relative report Python did not use the caller's venv: {error}")
            self.assertTrue((root / "output" / result["zip"]).is_file())

    def test_bare_report_python_is_found_on_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            caller = root / "caller"
            directory, executable = self.make_report_python(caller)
            search = str(executable.parent) + os.pathsep + os.environ.get("PATH", "")
            with contextlib.chdir(caller), patch.dict(os.environ, {"PATH": search}):
                result = self.build(root, report_python=executable.name, expected_prefix=directory)
            self.assertTrue((root / "output" / result["zip"]).is_file())

    def test_commit_archive_supplies_both_source_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.build(root)
            directory = root / "output" / result["package"]
            self.assertEqual((directory / "ma_nguon/README.md").read_text(), "committed snapshot")
            self.assertIn(b"committed snapshot", (directory / "bao_cao/BaoCao_Nhom2_NASA24.pdf").read_bytes())
            self.assertFalse((directory / "ma_nguon/data/processed").exists())
            manifest = packager.verify_payload(directory)
            self.assertEqual(manifest["source_commit"], COMMIT)
            self.assertEqual(manifest["report_pending_markers"]["01_test.md"], 1)
            with zipfile.ZipFile(root / "output" / result["zip"]) as archive:
                self.assertIsNone(archive.testzip())
                self.assertIn(result["package"] + "/manifest.json", archive.namelist())
            sidecar = (root / "output" / (result["zip"] + ".sha256")).read_text()
            self.assertEqual(sidecar, result["zip_sha256"] + "  " + result["zip"] + "\n")

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            out.mkdir()
            marker = out / "keep.txt"
            marker.write_bytes(b"keep")
            with patch.object(packager, "git_output") as git:
                with self.assertRaises(FileExistsError):
                    packager.package_commit(Path(tmp), "selected", out)
                git.assert_not_called()
            self.assertEqual(marker.read_bytes(), b"keep")

    def test_missing_pdf_even_after_exit_zero_does_not_publish_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "cả DOCX và PDF"):
                self.build(root, missing_pdf=True)
            self.assertEqual(list((root / "output").glob("*.zip")), [])

    def test_failed_report_does_not_publish_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(subprocess.CalledProcessError) as error:
                self.build(root, failed_build=True)
            self.assertEqual(error.exception.returncode, 9)
            self.assertEqual(list((root / "output").glob("*.zip")), [])

    def test_bundle_hash_mismatch_stops_before_report_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "Bundle khác"):
                self.build(root, bad_bundle=True)
            self.assertFalse((root / "output/build_report.log").exists())

    def test_archive_rejects_escape_and_symlink(self):
        for name, kind in [("../escape", tarfile.REGTYPE), ("link", tarfile.SYMTYPE)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                raw = io.BytesIO()
                with tarfile.open(fileobj=raw, mode="w") as archive:
                    info = tarfile.TarInfo(name)
                    info.type, info.linkname = kind, "../../outside"
                    archive.addfile(info)
                with self.assertRaisesRegex(ValueError, "không hợp lệ"):
                    packager.extract_archive(raw.getvalue(), Path(tmp) / "source")
                self.assertFalse((Path(tmp) / "source").exists())

    def test_manifest_detects_changed_or_extra_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.build(root)
            directory = root / "output" / result["package"]
            target = directory / "ma_nguon/README.md"
            original = target.read_bytes()
            target.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "manifest SHA-256"):
                packager.verify_payload(directory)
            target.write_bytes(original)
            (directory / "extra.txt").write_bytes(b"extra")
            with self.assertRaisesRegex(ValueError, "manifest SHA-256"):
                packager.verify_payload(directory)

    def test_crc_failure_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "crc.zip"
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
                archive.writestr("probe.txt", b"payload")
            raw = bytearray(path.read_bytes())
            name_size, extra_size = struct.unpack_from("<HH", raw, 26)
            raw[30 + name_size + extra_size] ^= 1
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "ZIP hỏng: probe.txt"):
                packager.check_zip(path)


if __name__ == "__main__":
    unittest.main()
