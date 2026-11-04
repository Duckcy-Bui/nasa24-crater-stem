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
REPOSITORY = "https://github.com/Duckcy-Bui/nasa24-crater-stem"
DELIVERABLES = {
    "slides": ("slide", "Hưng", "15–20 slide"),
    "video": ("video", "Quốc Anh", "5–7 phút"),
    "peer_review": ("danh_gia_cheo", "Cả nhóm", "Bảng đánh giá chéo thành viên"),
    "signed_assignment": (
        "phan_cong_ky",
        "Cả nhóm",
        "Bảng phân công, tỷ lệ đóng góp và chữ ký cả nhóm",
    ),
}


def sha256(path: Path) -> str:
    """Băm file trong gói bàn giao.

    Vào: path cần đọc. Ra: SHA-256 dạng hex; không ghi file, không có công thức báo cáo.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_output(repo: Path, *args: str) -> bytes:
    """Đọc stdout của một lệnh Git tại repo đã chọn.

    Vào: repo và các args Git. Ra: bytes stdout; lỗi tiến trình được truyền cho caller.
    Công thức báo cáo: không áp dụng cho truy xuất nguồn.
    """
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE)


def extract_archive(raw: bytes, destination: Path) -> None:
    """Giải TAR Git vào thư mục mới sau khi kiểm từng thành phần.

    Vào: raw là byte TAR, destination chưa tồn tại. Ra: None; ghi file/thư mục và giữ byte/quyền
    file.
    Từ chối đường dẫn vượt gốc và loại file khác thường; không có công thức toán.
    """
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        members = archive.getmembers()
        for member in members:
            name = PurePosixPath(member.name)
            if (
                name.is_absolute()
                or ".." in name.parts
                or "\\" in member.name
                or ":" in member.name
                or not (member.isdir() or member.isfile())
            ):
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
    """Lập bảng kích thước/hash của mọi file trong một thư mục.

    Vào: directory. Ra: dict đường dẫn tương đối→bytes/SHA-256; từ chối symlink, không ghi file.
    Công thức báo cáo: không áp dụng cho kiểm toàn vẹn.
    """
    result = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Không nhận symlink trong gói: {path.name}")
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
    return result


def check_zip(path: Path) -> None:
    """Kiểm CRC của tất cả thành phần ZIP.

    Vào: path ZIP. Ra: None khi testzip không tìm lỗi, ValueError nếu có thành phần hỏng.
    Không kiểm nội dung học thuật; công thức báo cáo không áp dụng.
    """
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
    if bad is not None:
        raise ValueError(f"ZIP hỏng: {bad}")


def verify_bundle(source: Path) -> dict:
    """Kiểm ZIP ảnh trong snapshot theo manifest đã lưu.

    Vào: source là gốc mã đã trích. Ra: dict đường dẫn bundle/hash/số file sau kiểm CRC, kích
    thước/hash.
    Đọc thành phần ZIP vào bộ nhớ để kiểm SHA, không trích file ra đĩa và không kiểm lại số
    học ảnh; dữ liệu mục 4.2, không có công thức mới.
    """
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
        if len(archive.namelist()) != len(set(archive.namelist())) or set(
            archive.namelist()
        ) != set(manifest["files"]):
            raise ValueError("Danh sách file bundle không khớp manifest")
        for name, expected in manifest["files"].items():
            payload = archive.read(name)
            if (
                len(payload) != expected["bytes"]
                or hashlib.sha256(payload).hexdigest() != expected["sha256"]
            ):
                raise ValueError(f"File trong bundle khác hash: {name}")
    return {
        "path": "ma_nguon/" + path.relative_to(source).as_posix(),
        "sha256": info["sha256"],
        "files_verified": len(manifest["files"]),
    }


def validate_reports(directory: Path) -> list[Path]:
    """Kiểm cấu trúc tối thiểu của DOCX và PDF đã dựng.

    Vào: directory chứa hai file REPORT_NAME. Ra: list Path DOCX/PDF hoặc ValueError.
    Kiểm CRC/phần Word và magic/EOF PDF; không kiểm số trang/nội dung, không có công thức toán.
    """
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
    """Đối chiếu toàn bộ file payload với manifest của gói.

    Vào: directory có manifest.json. Ra: manifest nếu kích thước/hash đều khớp, bỏ chính manifest.
    Không ghi file hoặc nghiệm thu nội dung; công thức không áp dụng.
    """
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    actual = inventory(directory)
    actual.pop("manifest.json")
    if actual != manifest["files"]:
        raise ValueError("Nội dung gói không khớp manifest SHA-256")
    return manifest


def pending_markers(source: Path) -> dict:
    """Đếm dấu chờ trong các chương nguồn, bỏ comment HTML.

    Vào: source là gốc snapshot có docs/bao_cao. Ra: dict tên chương→số dấu chờ; không ghi file.
    Công thức báo cáo: không áp dụng cho kiểm văn bản.
    """
    result = {}
    for path in sorted((source / "docs/bao_cao").glob("[0-9][0-9]_*.md")):
        text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
        result[path.name] = len(re.findall(r"\[CHỜ[^\]]*\]", text))
    return result


def add_deliverables(directory: Path, supplied: dict[str, Path]) -> dict:
    """Nhận file bổ sung vào đúng ô vai trò và ghi trạng thái nhận.

    Vào: directory gói, supplied ánh xạ vai trò→file không rỗng; không nhận vai trò lạ.
    Ra: dict receipts; ghi san_pham<đuôi> và README.md vào các ô san_pham_bo_sung/.
    Trạng thái nhận không là duyệt nội dung/chữ ký; không có công thức toán.
    """
    if supplied.keys() - DELIVERABLES.keys():
        raise ValueError("Loại sản phẩm bổ sung không hợp lệ")
    paths = {role: Path(path).absolute() for role, path in supplied.items()}
    for role, path in paths.items():
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"Sản phẩm {role} phải là file có nội dung")
    receipts = {}
    for role, (folder, owner, requirement) in DELIVERABLES.items():
        target = directory / "san_pham_bo_sung" / folder
        target.mkdir(parents=True)
        receipt = {"owner": owner, "requirement": requirement, "status": "missing", "path": None}
        if role in paths:
            artifact = target / ("san_pham" + paths[role].suffix)
            shutil.copyfile(paths[role], artifact)
            receipt.update(
                status="received_not_reviewed",
                path=artifact.relative_to(directory).as_posix(),
                bytes=artifact.stat().st_size,
                sha256=sha256(artifact),
            )
        note = (
            f"# {requirement}\n\nChủ phần: {owner}. Trạng thái: "
            f"`{receipt['status']}`.\n\nREADME này chỉ giữ chỗ. File đã nhận vẫn cần chủ "
            f"phần kiểm nội dung, số slide/thời lượng, đánh giá hoặc chữ ký thật; không "
            f"xác nhận thay thành viên.\n"
        )
        (target / "README.md").write_text(note, encoding="utf-8")
        receipts[role] = receipt
    return receipts


def package_commit(
    repo: Path,
    commit: str,
    output: Path,
    report_python: str = sys.executable,
    *,
    supplements: dict[str, Path] | None = None,
) -> dict:
    # Giữ symlink của venv; tên lệnh đơn vẫn được tìm qua PATH.
    """Tạo gói bàn giao từ đúng một commit Git và các file bổ sung đã nhận.

    Vào: repo, commit, output mới, report_python và supplements tùy chọn.
    Ra: dict kết quả; ghi mã archive, DOCX/PDF, guide, manifest, ZIP/checksum, log và result.json.
    Kiểm hash/CRC và giữ nguồn snapshot; submission_ready vẫn False, không có công thức toán.
    """
    report_python = os.fspath(report_python)
    # Resolve PATH before launching: Windows may prefer the parent Python executable.
    # abspath below preserves venv symlinks, unlike Path.resolve().
    if not os.path.dirname(report_python):
        report_python = shutil.which(report_python) or report_python
    if os.path.dirname(report_python):
        report_python = os.path.abspath(report_python)
    repo, output = repo.resolve(), output.resolve()
    if output.exists():
        raise FileExistsError(f"Thư mục đầu ra đã tồn tại, không ghi đè: {output}")
    revision = (
        git_output(repo, "rev-parse", "--verify", "--end-of-options", commit + "^{commit}")
        .decode()
        .strip()
    )
    tree = git_output(repo, "rev-parse", revision + "^{tree}").decode().strip()
    raw = git_output(repo, "archive", "--format=tar", revision)
    output.mkdir(parents=True)
    directory = output / ("NASA24_Nhom2_" + revision[:12])
    directory.mkdir()
    source = directory / "ma_nguon"
    extract_archive(raw, source)
    for name in [
        "README.md",
        "requirements.txt",
        "requirements-test.txt",
        "app.py",
        "scripts/build_report.py",
    ]:
        if not (source / name).is_file():
            raise ValueError(f"Commit thiếu đầu vào đóng gói: {name}")
    source_before = inventory(source)
    bundle = verify_bundle(source)
    deliverables = add_deliverables(directory, supplements or {})
    missing = [role for role, receipt in deliverables.items() if receipt["status"] == "missing"]

    build = output / "report_build"
    build.mkdir()
    command = [
        str(report_python),
        "-X",
        "utf8",
        "-B",
        str(source / "scripts/build_report.py"),
        "--out",
        str(build),
    ]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "MPLBACKEND": "Agg"}
    with (output / "build_report.log").open("w", encoding="utf-8") as log:
        subprocess.run(
            command, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT, check=True
        )
    reports = validate_reports(build)
    if inventory(source) != source_before:
        raise ValueError("Nguồn từ git archive bị thay đổi trong lúc dựng báo cáo")
    report_directory = directory / "bao_cao"
    report_directory.mkdir()
    for path in reports:
        shutil.copyfile(path, report_directory / path.name)

    guide = f"""# Gói bàn giao NASA 24 · Nhóm 2

Mã nguồn và nguồn báo cáo lấy bằng git archive từ commit `{revision}`.
Repo Git để xem lịch sử/đóng góp: {REPOSITORY} (commit `{revision}`).
PDF trong `bao_cao/` là định dạng nộp bắt buộc; DOCX là bản chỉnh sửa kèm theo.
Hai bản được dựng bằng script của chính commit đó; số trang cần kiểm riêng (30–60).
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
`san_pham_bo_sung/` có chỗ cho slide, video, đánh giá chéo và phân công có chữ ký.
Trạng thái nhận từng file ở `deliverables` trong manifest; file nhận ngoài commit được băm riêng.
Sản phẩm chưa nhận: {', '.join(missing) or 'không còn ô thiếu file; vẫn chờ kiểm nội dung'}.
README giữ chỗ không phải sản phẩm đã nộp; nhận file không xác nhận số slide, thời \
lượng hay chữ ký.
Các dấu chờ trong báo cáo được đếm trong manifest; dựng thành công không phải nghiệm thu nội dung.
Khảo sát ít nhất 10 học sinh chưa thực hiện theo quyết định 31/10/2026.
Theo Quy định BTL Xử lý ảnh: bảo vệ 20 phút (12 trình bày, 3 demo, 5 vấn đáp);
giảng viên chỉ định người trả lời, mọi người cần hiểu cả phần của thành viên khác.
Trưởng nhóm chốt đầu ra; nơi nộp, hạn và tên tệp vẫn chờ giảng viên, hai tài liệu học \
phần không ghi.
"""
    (directory / "HUONG_DAN_BAN_GIAO.md").write_text(guide, encoding="utf-8")
    manifest = {
        "schema_version": "s316-package-2",
        "status": "complete",
        "submission_ready": False,
        "scope": "Mã, báo cáo, hướng dẫn và bundle; chưa nghiệm thu bộ nộp cuối.",
        "source_repository": REPOSITORY,
        "source_commit": revision,
        "source_tree": tree,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "packager_sha256": sha256(Path(__file__)),
        "source_files": len(source_before),
        "report_build_script_sha256": source_before["scripts/build_report.py"]["sha256"],
        "report_pending_markers": pending_markers(source),
        "deliverables": deliverables,
        "required_deliverables_missing": missing,
        "external_deliverables_not_checked": [
            "slide",
            "video",
            "đánh giá chéo",
            "phân công có chữ ký",
            "xác nhận thành viên",
        ],
        "submission_checks_not_performed": [
            "PDF 30–60 trang",
            "15–20 slide",
            "Video 5–7 phút",
            "Nội dung, đánh giá và chữ ký thật",
            "Liêm chính học thuật",
            "Tổng duyệt 20 phút",
        ],
        "dataset_bundle": bundle,
        "files": inventory(directory),
    }
    (directory / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
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
        if (
            len(archive.namelist()) != len(expected_names)
            or set(archive.namelist()) != expected_names
        ):
            raise ValueError("ZIP thiếu/thừa file so với gói đã kiểm")
        for name, expected in expected_files.items():
            raw = archive.read(directory.name + "/" + name)
            if (
                len(raw) != expected["bytes"]
                or hashlib.sha256(raw).hexdigest() != expected["sha256"]
            ):
                raise ValueError(f"ZIP khác manifest: {name}")
    partial.rename(archive_path)
    archive_hash = sha256(archive_path)
    archive_path.with_suffix(".zip.sha256").write_text(
        f"{archive_hash}  {archive_path.name}\n", encoding="utf-8"
    )
    result = {
        "source_commit": revision,
        "package": directory.name,
        "zip": archive_path.name,
        "zip_sha256": archive_hash,
        "payload_files": len(manifest["files"]),
        "source_files": len(source_before),
        "zip_crc": "pass",
        "payload_sha256": "pass",
        "submission_ready": False,
        "required_deliverables_missing": missing,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv=None) -> int:
    """Đọc CLI và đóng gói snapshot cùng sản phẩm bổ sung.

    Vào: argv chọn commit, output, report-python, slide/video/đánh giá chéo/phân công ký.
    Ra: mã 0/1; ghi gói qua package_commit, in ZIP/checksum hoặc lỗi ra stderr.
    Phụ lục A và hướng dẫn bàn giao; không tự nghiệm thu hoặc áp dụng công thức thuật toán ảnh.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commit", required=True, help="Commit đã chốt; không lấy file chưa commit"
    )
    parser.add_argument("--output", type=Path, required=True, help="Thư mục mới, không ghi đè")
    parser.add_argument(
        "--report-python", default=sys.executable, help="Python đã cài requirements-report.txt"
    )
    parser.add_argument(
        "--slides", type=Path, help="Slide do chủ phần bàn giao; vẫn cần kiểm 15–20 slide"
    )
    parser.add_argument(
        "--video", type=Path, help="Video do chủ phần bàn giao; vẫn cần kiểm 5–7 phút"
    )
    parser.add_argument(
        "--peer-review", type=Path, help="Bảng đánh giá chéo thành viên, không tự điền"
    )
    parser.add_argument(
        "--signed-assignment", type=Path, help="Bảng phân công có chữ ký thật của cả nhóm"
    )
    args = parser.parse_args(argv)
    try:
        supplements = {
            role: getattr(args, role) for role in DELIVERABLES if getattr(args, role) is not None
        }
        result = package_commit(
            ROOT, args.commit, args.output, args.report_python, supplements=supplements
        )
    except (
        OSError,
        ValueError,
        KeyError,
        subprocess.CalledProcessError,
        tarfile.TarError,
        zipfile.BadZipFile,
    ) as error:
        print(f"Đóng gói thất bại: {error}", file=sys.stderr)
        return 1
    print(f"Complete: {args.output / result['zip']}")
    print(f"SHA-256: {result['zip_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
