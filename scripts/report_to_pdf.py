"""Đức — S3-12: mở DOCX bằng LibreOffice, cập nhật mục lục và số trang, xuất PDF.

Chạy bằng Python có module uno (python3 hệ thống trên Linux, hoặc
"C:\\Program Files\\LibreOffice\\program\\python.exe" trên Windows):
    python3 scripts/report_to_pdf.py outputs/report/BaoCao.docx outputs/report/BaoCao.pdf

scripts/build_report.py tự gọi script này khi tìm thấy LibreOffice.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import uno  # noqa: F401  (nạp bộ nối UNO trước khi import com.sun.star)
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException


def _prop(name: str, value) -> PropertyValue:
    prop = PropertyValue()
    prop.Name, prop.Value = name, value
    return prop


def _soffice() -> str:
    for candidate in ("soffice", r"C:\Program Files\LibreOffice\program\soffice.exe",
                      "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        found = shutil.which(candidate) or (candidate if Path(candidate).exists() else None)
        if found:
            return found
    raise SystemExit("Không tìm thấy soffice (LibreOffice).")


def convert(source: Path, target: Path) -> None:
    pipe = f"nasa24_report_{int(time.time() * 1000)}"
    profile = tempfile.mkdtemp(prefix="nasa24_lo_")
    try:
        # Hồ sơ riêng để không đụng LibreOffice đang mở của người dùng.
        office = subprocess.Popen([_soffice(), "--headless", "--invisible", "--norestore", "--nologo",
                                   f"-env:UserInstallation={Path(profile).as_uri()}",
                                   f"--accept=pipe,name={pipe};urp;StarOffice.ComponentContext"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            local = uno.getComponentContext()
            resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
            for _ in range(120):
                try:
                    context = resolver.resolve(f"uno:pipe,name={pipe};urp;StarOffice.ComponentContext")
                    break
                except NoConnectException:
                    time.sleep(0.5)
            else:
                raise SystemExit("LibreOffice không khởi động được.")
            desktop = context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", context)
            document = desktop.loadComponentFromURL(source.resolve().as_uri(), "_blank", 0, (_prop("Hidden", True),))
            if document is None:
                raise SystemExit(f"LibreOffice không mở được {source}.")
            try:
                # Hai lượt: lượt đầu điền mục lục làm dời trang, lượt sau ghi lại số trang đúng.
                for _ in range(2):
                    indexes = document.getDocumentIndexes()
                    for i in range(indexes.getCount()):
                        indexes.getByIndex(i).update()
                    document.getTextFields().refresh()
                    document.refresh()
                document.storeToURL(target.resolve().as_uri(), (_prop("FilterName", "writer_pdf_Export"),))
            finally:
                document.close(True)
            try:
                desktop.terminate()
            except Exception:  # LibreOffice có thể ngắt kết nối khi tự thoát
                pass
        finally:
            try:
                office.wait(timeout=20)
            except subprocess.TimeoutExpired:
                office.kill()
    finally:
        # Trên Windows, LibreOffice có thể còn giữ file vài giây sau khi thoát; bỏ qua lỗi dọn thư mục tạm.
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
