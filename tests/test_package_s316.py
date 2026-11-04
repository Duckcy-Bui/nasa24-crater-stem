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
REQUIRED_DELIVERABLES = {
    "slides": "slide",
    "video": "video",
    "peer_review": "danh_gia_cheo",
    "signed_assignment": "phan_cong_ky",
}
DELIVERABLE_FLAGS = {
    "--slides": "slides",
    "--video": "video",
    "--peer-review": "peer_review",
    "--signed-assignment": "signed_assignment",
}
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
             "requirements.txt": b"streamlit", "app.py": b"# demo entry point\n",
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
    def build(self, root, report_python=sys.executable, supplements=None, **options):
        repo = root / "live"
        repo.mkdir(exist_ok=True)
        (repo / "README.md").write_text("uncommitted working tree")
        (repo / "scripts").mkdir(exist_ok=True)
        (repo / "scripts/build_report.py").write_text("raise SystemExit('wrong source')")
        with patch.object(packager, "git_output", side_effect=git_fixture(snapshot(**options))):
            return packager.package_commit(repo, "selected", root / "output", report_python,
                                           supplements=supplements)

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

    def test_bare_report_python_is_resolved_before_subprocess(self):
        # Windows không tra PATH trước cho tên lệnh đơn; package_commit phải tự tra.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory, executable = self.make_report_python(root / "caller")
            with patch.object(packager.shutil, "which", return_value=str(executable)) as which:
                result = self.build(root, report_python="python-chi-co-qua-which",
                                    expected_prefix=directory)
            which.assert_called_once_with("python-chi-co-qua-which")
            self.assertTrue((root / "output" / result["zip"]).is_file())

    def test_missing_bare_report_python_fails_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(FileNotFoundError, "report_python"):
                self.build(root, report_python="khong-co-python-nay-tren-path")
            self.assertFalse((root / "output").exists())

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

    def test_draft_has_slots_and_records_missing_deliverables(self):
        self.assertEqual(set(packager.DELIVERABLES), set(REQUIRED_DELIVERABLES))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.build(root)
            directory = root / "output" / result["package"]
            manifest = packager.verify_payload(directory)
            self.assertIs(manifest["submission_ready"], False)
            self.assertIs(result["submission_ready"], False)
            self.assertEqual(set(manifest["deliverables"]), set(REQUIRED_DELIVERABLES))
            self.assertEqual(set(manifest["required_deliverables_missing"]), set(REQUIRED_DELIVERABLES))
            self.assertEqual(set(result["required_deliverables_missing"]), set(REQUIRED_DELIVERABLES))
            self.assertEqual(manifest["source_repository"], packager.REPOSITORY)
            for role, folder in REQUIRED_DELIVERABLES.items():
                self.assertEqual(manifest["deliverables"][role]["status"], "missing")
                self.assertIsNone(manifest["deliverables"][role]["path"])
                self.assertTrue((directory / "san_pham_bo_sung" / folder / "README.md").is_file())

    def test_received_files_are_hashed_without_claiming_owner_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            supplied = {}
            for role in REQUIRED_DELIVERABLES:
                path = root / ("private-author-" + role + ".fixture")
                path.write_bytes(role.encode())
                supplied[role] = path
            result = self.build(root, supplements=supplied)
            directory = root / "output" / result["package"]
            manifest = packager.verify_payload(directory)
            self.assertEqual(set(manifest["deliverables"]), set(REQUIRED_DELIVERABLES))
            self.assertEqual(manifest["required_deliverables_missing"], [])
            self.assertEqual(result["required_deliverables_missing"], [])
            self.assertIs(manifest["submission_ready"], False)
            self.assertIs(result["submission_ready"], False)
            self.assertNotIn(str(root), (directory / "manifest.json").read_text())
            for role, path in supplied.items():
                receipt = manifest["deliverables"][role]
                self.assertEqual(receipt["status"], "received_not_reviewed")
                self.assertEqual((directory / receipt["path"]).read_bytes(), path.read_bytes())
                self.assertEqual(receipt["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertNotIn(path.name, receipt["path"])
                self.assertIn(receipt["path"], manifest["files"])
                with zipfile.ZipFile(root / "output" / result["zip"]) as archive:
                    self.assertEqual(archive.read(result["package"] + "/" + receipt["path"]), path.read_bytes())

    def test_partial_delivery_keeps_other_slots_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            slides = root / "slides.pdf"
            slides.write_bytes(b"owner slide fixture")
            result = self.build(root, supplements={"slides": slides})
            directory = root / "output" / result["package"]
            manifest = packager.verify_payload(directory)
            self.assertIs(manifest["submission_ready"], False)
            self.assertIs(result["submission_ready"], False)
            self.assertEqual(set(manifest["deliverables"]), set(REQUIRED_DELIVERABLES))
            for record in (manifest, result):
                self.assertEqual(set(record["required_deliverables_missing"]),
                                 {"video", "peer_review", "signed_assignment"})

    def test_invalid_deliverable_does_not_publish_zip(self):
        for kind in ("missing", "empty", "directory", "unknown_role"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                path = root / "owner-file"
                if kind == "empty":
                    path.write_bytes(b"")
                elif kind == "directory":
                    path.mkdir()
                elif kind == "unknown_role":
                    path.write_bytes(b"owner fixture")
                role = "typo" if kind == "unknown_role" else "slides"
                with self.assertRaisesRegex(ValueError, "không hợp lệ|phải là file có nội dung"):
                    self.build(root, supplements={role: path})
                self.assertEqual(list((root / "output").glob("*.zip")), [])
                self.assertFalse((root / "output/build_report.log").exists())

    def test_cli_passes_owner_deliverables_to_packager(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = ["--commit", "selected", "--output", str(root / "output")]
            expected = {}
            for flag, role in DELIVERABLE_FLAGS.items():
                path = root / (role + ".fixture")
                args += [flag, str(path)]
                expected[role] = path
            with patch.object(packager, "package_commit", return_value={"zip": "fixture.zip", "zip_sha256": "test"}) as call:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(packager.main(args), 0)
            self.assertEqual(call.call_args.kwargs["supplements"], expected)

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
