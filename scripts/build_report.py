"""Đức — S3-12: ghép báo cáo từ docs/bao_cao/*.md thành DOCX và PDF.

Định dạng theo yêu cầu môn: A4, Times New Roman 13, giãn dòng 1,3. Lề trái
3 cm, phải 2 cm, trên/dưới 2,5 cm, số trang ở chân trang. Mỗi chương bắt đầu trang mới.

Cách chạy:
    pip install -r requirements-report.txt
    python scripts/build_report.py            # DOCX, và PDF nếu tìm thấy LibreOffice
    python scripts/build_report.py --no-pdf   # chỉ DOCX (mở bằng Word, F9 để cập nhật mục lục)

Đầu ra nằm trong outputs/report/ (không commit). Thứ tự ghép là thứ tự tên file
trong docs/bao_cao/ (00_..., 01_..., ...); README.md không được ghép.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "bao_cao"
OUTPUT = ROOT / "outputs" / "report"
NAME = "BTL_XLA"
FONT = "Times New Roman"


PENDING = re.compile(r"\[CHỜ[^\]]*\]")


def chapters(only: list[str] | None = None) -> list[Path]:
    """Chọn các chương Markdown theo thứ tự ghép báo cáo.

    Vào: only là danh sách tiền tố NN hoặc None; đọc SOURCE, luôn giữ phần 00 khi lọc.
    Ra: list Path; SystemExit khi bộ chọn sai/rỗng. Phụ lục A, không có công thức toán.
    """
    files = sorted(p for p in SOURCE.glob("[0-9][0-9]_*.md"))
    if only:
        unknown = sorted(set(only) - {p.name[:2] for p in files})
        if unknown:
            raise SystemExit(
                f"Không có file chương số {', '.join(unknown)} (ghi hai chữ số, ví dụ --only 03)."
            )
        files = [p for p in files if p.name[:2] == "00" or p.name[:2] in only]
    if not files:
        raise SystemExit(f"Không có chương nào trong {SOURCE.relative_to(ROOT)}.")
    return files


# LibreOffice bỏ khoảng trắng TeX (\qquad) và thu hẹp em-space khi đọc công thức Word, nên số công
# thức
# dính vào công thức. Khi ghép, đổi "\qquad (2.1)" ở cuối công thức thành 8 khoảng trắng không ngắt
# (U+00A0);
# Word cũng hiển thị đúng.
EQUATION_NUMBER = re.compile(r"\\q?quad\s*(\((?:\d+|[A-Z])\.\d+\))\s*(?=\$\$)")


REPO_BLOB = "https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/"
INLINE_LINK = re.compile(r'(?<!!)\[([^\]]+)\]\((\.\./[^)\s]+)((?:\s+"[^"]*")?)\)')
REFERENCE_LINK = re.compile(r"^( {0,3}\[[^\]]+\]:\s*)(\.\./\S+)", re.M)
CODE_SPLIT = re.compile(r"(^```.*?^```[^\n]*$|`[^`\n]*`)", re.M | re.S)


def _repo_url(relative: str) -> str:
    """Đổi đường dẫn tương đối tính từ docs/bao_cao/ thành URL blob/main trên GitHub.

    Vào: relative như ../evidence/x.csv. Ra: URL công khai. Phát ValueError nếu đường dẫn
    đi ra ngoài gốc repo.
    """
    parts: list[str] = []
    for piece in ("docs/bao_cao/" + relative).split("/"):
        if piece == "..":
            if not parts:
                raise ValueError(f"Liên kết ra ngoài repo: {relative}")
            parts.pop()
        elif piece not in ("", "."):
            parts.append(piece)
    return REPO_BLOB + "/".join(parts)


def public_links(text: str) -> str:
    """Đổi liên kết tương đối ra ngoài docs/bao_cao thành URL GitHub công khai.

    Vào: text Markdown của một chương trong docs/bao_cao/. Ra: chuỗi đã đổi. Đổi liên kết
    inline (kể cả có tiêu đề) và định nghĩa liên kết tham chiếu; giữ nguyên ảnh (![...]),
    inline code và khối code. Nếu để tương đối, LibreOffice ghi URI file:// tuyệt đối của
    máy dựng vào PDF.
    """
    def convert(segment: str) -> str:
        segment = INLINE_LINK.sub(
            lambda m: f"[{m.group(1)}]({_repo_url(m.group(2))}{m.group(3)})", segment)
        return REFERENCE_LINK.sub(lambda m: m.group(1) + _repo_url(m.group(2)), segment)

    pieces = CODE_SPLIT.split(text)
    return "".join(piece if i % 2 else convert(piece) for i, piece in enumerate(pieces))


def combined_markdown(files: list[Path]) -> str:
    """Ghép chương, sinh danh mục hình/bảng và xử lý khoảng cách số công thức.

    Vào: files là các Path Markdown theo thứ tự. Ra: chuỗi Markdown đã ghép; không ghi file.
    Chỉ thay cách trình bày số công thức bằng khoảng trắng không ngắt, không tính lại công thức.
    """
    sources = [public_links(f.read_text(encoding="utf-8")) for f in files]
    captions = re.findall(
        r"(?:!\[|^: )(Hình \d+\.\d+|Bảng [\dA-Z]+\.\d+)\. ([^\n]+)", "\n".join(sources), flags=re.M
    )
    rows = ["| Hình/bảng | Nội dung | Trang |", "|---|---|---:|"]
    for label, caption in captions:
        title = caption.split("](", 1)[0].split(". ", 1)[0].replace("`", "")
        title = re.split(r"[;:]", title, maxsplit=1)[0]
        if len(title) > 58:
            title = title[:55].rsplit(" ", 1)[0] + "…"
        rows.append(f"| {label} | {title.rstrip('.')} | 0 |")
    listing = "\n".join(rows)
    parts = [
        EQUATION_NUMBER.sub(
            lambda m: "\\text{" + "\u00a0" * 8 + "}" + m.group(1) + " ",
            text.replace("<!-- REPORT_LISTS -->", listing),
        )
        for text in sources
    ]
    return "\n\n".join(parts)


def report_status(files: list[Path]) -> None:
    """In số chữ và các dấu chờ trong những chương được chọn.

    Vào: files là các Path Markdown. Ra: None; ghi thống kê ra stdout, bỏ comment HTML khi đếm.
    Công thức báo cáo: không áp dụng cho kiểm văn bản.
    """
    total = 0
    for path in files:
        text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
        words = len(re.findall(r"\w+", text))
        total += words
        pending = PENDING.findall(text)
        print(
            f"  {path.name:<40} {words:>6} chữ"
            + (f" · {len(pending)} chỗ [CHỜ]" if pending else "")
        )
    print(f"  {'Tổng':<40} {total:>6} chữ")


def _font(
    style, size: float | None = None, *, bold: bool | None = None, italic: bool | None = None
) -> None:
    """Đặt phông chữ và thuộc tính định dạng của một style DOCX.

    Vào: style, size tùy chọn và cờ bold/italic; dùng FONT của mô-đun.
    Ra: None; sửa style tại chỗ, gồm phông các bộ ký tự và màu đen; không có công thức toán.
    """
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor

    style.font.name = FONT
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(fonts)
    for key in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(key), FONT)
    for key in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        fonts.attrib.pop(qn(key), None)
    if size is not None:
        style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    style.font.color.rgb = RGBColor(0, 0, 0)


def _page_number_footer(section) -> None:
    """Thêm trường số trang căn giữa ở chân trang DOCX.

    Vào: section cần sửa. Ra: None; cập nhật footer bằng trường PAGE, không ghi file trực tiếp.
    Định dạng Phụ lục A, không có công thức toán.
    """
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn

    paragraph = (
        section.footer.paragraphs[0]
        if section.footer.paragraphs
        else section.footer.add_paragraph()
    )
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    for kind, text in (
        ("begin", None),
        (None, " PAGE "),
        ("separate", None),
        (None, "1"),
        ("end", None),
    ):
        if kind:
            element = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): kind})
        elif text.strip() == "PAGE":
            element = run._r.makeelement(qn("w:instrText"), {qn("xml:space"): "preserve"})
            element.text = text
        else:
            element = run._r.makeelement(qn("w:t"), {})
            element.text = text
        run._r.append(element)


def reference_docx(pandoc: str, target: Path) -> Path:
    """Tạo mẫu DOCX theo quy cách trình bày của báo cáo.

    Vào: pandoc là chương trình xuất mẫu, target là file mẫu đích.
    Ra: Path target; ghi DOCX có style, lề, khổ giấy và trường số trang.
    Định dạng Phụ lục A, không có công thức toán.
    """
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt

    raw = subprocess.run(
        [pandoc, "--print-default-data-file", "reference.docx"], check=True, capture_output=True
    ).stdout
    target.write_bytes(raw)
    document = Document(str(target))
    styles = document.styles
    body = ("Normal", "Body Text", "First Paragraph", "Compact", "Block Text", "Footnote Text")
    for name in body:
        if name in styles:
            _font(styles[name], 13)
            fmt = styles[name].paragraph_format
            fmt.line_spacing = 1.3
            fmt.space_before = Pt(0)
            fmt.space_after = Pt(6)
    for name in ("Body Text", "First Paragraph"):
        styles[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        styles[name].paragraph_format.first_line_indent = Cm(1)
    styles["Compact"].paragraph_format.space_after = Pt(2)
    styles["Block Text"].paragraph_format.left_indent = Cm(1)
    for level, size in ((1, 16), (2, 14), (3, 13), (4, 13)):
        style = styles[f"Heading {level}"]
        _font(style, size, bold=True, italic=(level >= 3))
        fmt = style.paragraph_format
        fmt.line_spacing = 1.3
        fmt.space_before = Pt(18 if level == 1 else 12)
        fmt.space_after = Pt(12 if level == 1 else 6)
        fmt.keep_with_next = True
    styles["Heading 1"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    styles["Heading 1"].paragraph_format.page_break_before = True
    for name, size in (
        ("Title", 18),
        ("Subtitle", 15),
        ("Author", 13),
        ("Date", 13),
        ("Abstract", 13),
    ):
        if name in styles:
            _font(styles[name], size, bold=(name == "Title"))
            styles[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for name in ("Image Caption", "Table Caption", "Caption"):
        if name in styles:
            _font(styles[name], 12, italic=True)
            styles[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            styles[name].paragraph_format.space_after = Pt(10)
    for name in ("Captioned Figure", "Figure"):
        if name in styles:
            styles[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            styles[name].paragraph_format.keep_with_next = True
    if "Source Code" in styles:
        styles["Source Code"].font.size = Pt(10)
    # Kiểu cho trang bìa, dùng trong Markdown bằng ::: {custom-style="Cover Title"} ... :::
    from docx.enum.style import WD_STYLE_TYPE

    for name, size, bold, space in (
        ("Cover", 13, False, 4),
        ("Cover Strong", 14, True, 4),
        ("Cover Title", 18, True, 12),
        ("Cover Big", 22, True, 18),
    ):
        style = styles[name] if name in styles else styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = styles["Normal"]
        _font(style, size, bold=bold)
        style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        style.paragraph_format.first_line_indent = Cm(0)
        style.paragraph_format.space_after = Pt(space)
    if "TOC Heading" in styles:
        _font(styles["TOC Heading"], 16, bold=True)
        styles["TOC Heading"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for section in document.sections:
        section.page_width, section.page_height = Cm(21), Cm(29.7)
        section.left_margin, section.right_margin = Cm(3), Cm(2)
        section.top_margin, section.bottom_margin = Cm(2.5), Cm(2.5)
        section.footer_distance = Cm(1)
        _page_number_footer(section)
    document.save(str(target))
    return target


def build_docx(pandoc: str, output: Path, files: list[Path]) -> Path:
    """Dựng DOCX từ các chương Markdown với hình và trích dẫn.

    Vào: pandoc, output là file DOCX và files là các chương nguồn theo thứ tự.
    Ra: Path output; ghi reference.docx, _ghep.md, DOCX rồi hậu xử lý định dạng.
    Phụ lục A; giữ biểu thức báo cáo, không thực hiện phép tính trong chúng.
    """
    reference = reference_docx(pandoc, output.parent / "reference.docx")
    source = output.parent / "_ghep.md"
    source.write_text(combined_markdown(files), encoding="utf-8")
    command = [
        pandoc,
        str(source),
        "--from",
        'markdown+pipe_tables+grid_tables+tex_math_dollars+implicit_figures+f'
        'enced_divs+raw_attribute',
        "--to",
        "docx",
        "--reference-doc",
        str(reference),
        "--resource-path",
        os.pathsep.join(str(p) for p in (SOURCE, ROOT / "docs", ROOT)),
        "--no-highlight",  # mã in đen trắng; tùy chọn này có cả ở pandoc 2.x lẫn 3.x
        # Đường dẫn tương đối theo cwd=SOURCE: Pandoc ghi giá trị này vào docProps/custom.xml của
        # DOCX,
        # nên không truyền đường dẫn tuyệt đối của máy dựng.
        "--citeproc",
        "--bibliography",
        "tai_lieu.bib",
        "--csl",
        "ieee.csl",
        # Danh mục tài liệu theo IEEE bằng tiếng Anh (vol., no., pp.); ngôn ngữ văn bản đặt lại
        # vi-VN bên dưới.
        "--metadata",
        "lang=en-US",
        "--metadata",
        "link-citations=true",
        "--output",
        str(output),
    ]
    subprocess.run(command, check=True, cwd=SOURCE)
    _postprocess(output, "vi-VN")
    return output


def _postprocess(path: Path, language: str) -> None:
    """Chỉnh ngôn ngữ, bảng và trường chú thích trong DOCX vừa dựng.

    Vào: path là DOCX, language là mã ngôn ngữ. Ra: None; sửa và lưu lại file path.
    Định dạng Phụ lục A, không có công thức toán.
    """
    from docx import Document
    from docx.oxml.ns import qn

    document = Document(str(path))
    defaults = document.styles.element.find(qn("w:docDefaults"))
    rpr = defaults.find(qn("w:rPrDefault")).find(qn("w:rPr")) if defaults is not None else None
    if rpr is not None:
        lang = rpr.find(qn("w:lang"))
        if lang is None:
            lang = rpr.makeelement(qn("w:lang"), {})
            rpr.append(lang)
        lang.set(qn("w:val"), language)
    for table in document.tables:
        _polish_table(table)
        following = table._tbl.getnext()
        # chừa khoảng giữa bảng và đoạn sau
        if following is not None and following.tag == qn("w:p"):
            spacing = following.get_or_add_pPr().find(qn("w:spacing"))
            if spacing is None:
                spacing = following.get_or_add_pPr().makeelement(qn("w:spacing"), {})
                following.get_or_add_pPr().append(spacing)
            spacing.set(qn("w:before"), "160")
    _caption_page_fields(document)
    document.save(str(path))


def _caption_page_fields(document) -> None:
    """Gắn bookmark chú thích và trường PAGEREF cho danh mục hình/bảng.

    Vào: document là DOCX đang mở. Ra: None; sửa document tại chỗ, lỗi nếu danh mục thiếu đích.
    LibreOffice cập nhật số trang khi dựng; không có công thức toán.
    """
    from docx.oxml.ns import qn

    existing = document.element.findall(".//" + qn("w:bookmarkStart"))
    next_id = max((int(e.get(qn("w:id"))) for e in existing), default=0) + 1
    targets = {}
    for paragraph in document.paragraphs:
        match = re.match(r"^(Hình \d+\.\d+|Bảng [\dA-Z]+\.\d+)\.", paragraph.text)
        if not match or paragraph.style.name not in ("Image Caption", "Table Caption", "Caption"):
            continue
        label = match.group(1)
        name = "report_caption_" + re.sub(r"[^A-Za-z0-9]", "_", label)
        start = paragraph._p.makeelement(
            qn("w:bookmarkStart"), {qn("w:id"): str(next_id), qn("w:name"): name}
        )
        end = paragraph._p.makeelement(qn("w:bookmarkEnd"), {qn("w:id"): str(next_id)})
        paragraph._p.insert(1 if paragraph._p.pPr is not None else 0, start)
        paragraph._p.append(end)
        targets[label] = name
        next_id += 1
    for table in document.tables:
        if not table.rows or table.cell(0, 0).text != "Hình/bảng":
            continue
        for row in table.rows[1:]:
            label = row.cells[0].text
            if label not in targets:
                raise ValueError(f"Không tìm thấy chú thích cho danh mục: {label}")
            paragraph = row.cells[2].paragraphs[0]
            paragraph.clear()
            run = paragraph.add_run()
            for kind, text in (
                ("begin", None),
                (None, f" PAGEREF {targets[label]} \\h "),
                ("separate", None),
                (None, "0"),
                ("end", None),
            ):
                if kind:
                    element = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): kind})
                elif text == "0":
                    element = run._r.makeelement(qn("w:t"), {})
                    element.text = text
                else:
                    element = run._r.makeelement(qn("w:instrText"), {qn("xml:space"): "preserve"})
                    element.text = text
                run._r.append(element)


def _polish_table(table, text_width_cm: float = 16.0) -> None:
    """Căn bảng DOCX và chia bề rộng cột theo nội dung.

    Vào: table cần sửa, text_width_cm là tổng rộng; một số bảng có độ rộng cột cố định.
    Ra: None; sửa ô/cột, định dạng đoạn/chữ và hàng tiêu đề lặp lại tại chỗ.
    Đây là quy tắc dàn trang, không phải công thức thuật toán ảnh trong báo cáo.
    """
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt

    rows = table.rows
    columns = len(table.columns)
    if not rows or not columns:
        return
    # itertext() lấy cả chữ trong công thức (OMML), cell.text thì bỏ qua công thức.
    texts = [
        ["".join(cell._tc.itertext()).strip() for cell in row.cells[:columns]] for row in rows
    ]
    weight, longest = [], []
    for i in range(columns):
        column = [row[i] for row in texts if i < len(row)]
        weight.append(min(60.0, max(6.0, sum(len(t) for t in column) / len(column))))
        longest.append(max((len(word) for t in column for word in t.split()), default=1))
    widths = [text_width_cm * w / sum(weight) for w in weight]
    floor = [min(5.0, 0.22 * n + 0.4) for n in longest]  # khoảng 0,22 cm mỗi ký tự ở cỡ 12
    if (
        sum(floor) > text_width_cm
    ):  # quá nhiều cột hẹp: thu các mức sàn theo tỷ lệ để tổng vừa dòng
        floor = [f * text_width_cm / sum(floor) for f in floor]
    for _ in range(3):
        short = [max(f - w, 0.0) for w, f in zip(widths, floor)]
        if not any(short):
            break
        spare = [i for i in range(columns) if not short[i]]
        take = sum(short)
        room = sum(widths[i] - floor[i] for i in spare) or 1.0
        widths = [
            max(w, f) if short[i] else w - take * (w - floor[i]) / room
            for i, (w, f) in enumerate(zip(widths, floor))
        ]
    headers = [cell.text for cell in rows[0].cells]
    if headers == ["Hình/bảng", "Nội dung", "Trang"]:
        widths = [2.8, 11.4, 1.8]
    elif headers == [
        "Thành viên",
        "Công việc",
        "File mã chính",
        "Mục viết",
        "Tỷ lệ (%)",
        "Chữ ký",
    ]:
        widths = [2.2, 2.3, 5.0, 3.7, 1.3, 1.5]
    elif headers[:3] == ["Sprint", "Ngày họp", "Nội dung"] and columns == 4:
        widths = [2.4, 2.4, 7.2, 4.0]  # Bảng C.1: cột nội dung rộng nhất
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    for tag, attrs in (
        ("w:tblW", {"w:type": "dxa", "w:w": str(int(text_width_cm * 567))}),
        ("w:tblLayout", {"w:type": "fixed"}),
    ):
        element = tbl_pr.find(qn(tag))
        if element is None:
            element = tbl_pr.makeelement(qn(tag), {})
            tbl_pr.append(element)
        for key, value in attrs.items():
            element.set(qn(key), value)
    grid = tbl.tblGrid
    for col, width in zip(grid.findall(qn("w:gridCol")), widths):
        col.set(qn("w:w"), str(int(width * 567)))
    for r, row in enumerate(rows):
        if r == 0:
            tr_pr = row._tr.get_or_add_trPr()
            if tr_pr.find(qn("w:tblHeader")) is None:
                tr_pr.append(tr_pr.makeelement(qn("w:tblHeader"), {}))
        for i, cell in enumerate(row.cells[:columns]):
            cell.width = Cm(widths[i])
            for paragraph in cell.paragraphs:
                fmt = paragraph.paragraph_format
                if fmt.alignment is None:  # giữ căn phải/giữa do Markdown (---: / :---:) đặt
                    fmt.alignment = WD_ALIGN_PARAGRAPH.LEFT
                fmt.first_line_indent = Cm(0)
                fmt.line_spacing = 1.15
                fmt.space_before, fmt.space_after = Pt(2), Pt(2)
                for run in paragraph.runs:
                    run.font.size = Pt(12)
                    if r == 0:
                        run.font.bold = True


def uno_python() -> str | None:
    """Tìm Python có thể nạp bộ nối LibreOffice UNO.

    Vào: REPORT_UNO_PYTHON và các vị trí ứng viên trên hệ thống. Ra: chuỗi chương trình hoặc None.
    Thử import bằng tiến trình con; không ghi file, không có công thức toán.
    """
    candidates = [
        os.environ.get("REPORT_UNO_PYTHON"),
        "/usr/bin/python3",
        r"C:\Program Files\LibreOffice\program\python.exe",
        "/Applications/LibreOffice.app/Contents/Resources/python",
    ]
    for candidate in filter(None, candidates):
        if (
            Path(candidate).exists()
            and subprocess.run([candidate, "-c", "import uno"], capture_output=True).returncode
            == 0
        ):
            return candidate
    return None


def main(argv: list[str] | None = None) -> int:
    """Dựng báo cáo DOCX và tùy điều kiện xuất PDF từ lựa chọn CLI.

    Vào: argv chọn only, out và no-pdf; dùng nguồn chương, thư mục hình và tài liệu tham khảo.
    Ra: mã 0; ghi DOCX và file trung gian, gọi UNO xuất PDF khi được chọn và có bộ nối.
    Phụ lục A; không dùng kết quả dựng để xác nhận các dấu chờ.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-pdf", action="store_true", help="chỉ xuất DOCX")
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="NN",
        help="chỉ ghép trang đầu và các chương có số này, ví dụ --only 02 03",
    )
    parser.add_argument(
        "--out", type=Path, default=OUTPUT, help="thư mục đầu ra (mặc định outputs/report)"
    )
    args = parser.parse_args(argv)
    args.out = (
        args.out.resolve()
    )  # pandoc chạy trong docs/bao_cao, nên đường dẫn tương đối phải đổi trước
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    files = chapters(args.only)
    report_status(files)
    try:
        import pypandoc
    except ImportError:
        raise SystemExit("Thiếu pypandoc: pip install -r requirements-report.txt")
    pandoc = pypandoc.get_pandoc_path()
    args.out.mkdir(parents=True, exist_ok=True)
    docx = build_docx(pandoc, args.out / f"{NAME}.docx", files)
    print(f"DOCX: {docx}")
    if args.no_pdf:
        return 0
    python = uno_python()
    if python is None:
        print(
            'Không tìm thấy Python có module uno của LibreOffice (cài '
            'python3-uno, hoặc đặt REPORT_UNO_PYTHON);'
            " mở DOCX bằng Word, Ctrl+A rồi F9 cập nhật mục lục, sau đó lưu PDF."
        )
        return 0
    pdf = args.out / f"{NAME}.pdf"
    subprocess.run(
        [python, str(ROOT / "scripts" / "report_to_pdf.py"), str(docx), str(pdf)], check=True
    )
    print(f"PDF: {pdf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
