from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
CATALOG_HTML = ROOT / "catalog.html"
OUTPUT_PDF = ROOT / "price.pdf"

FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

CONTACTS = [
    "+38 (050) 751-92-43",
    "+38 (097) 428-69-00",
]

_CELL_SKIP = object()


def clean(text: str) -> str:
    return " ".join(text.replace("\n", " ").split())


class CatalogParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[tuple[str, list[list[str]]]] = []
        self.current_heading = ""
        self._in_heading = False
        self._heading_tag = ""
        self._heading_text: list[str] = []

        self._in_table = False
        self._in_thead = False
        self._grid: list[list[str]] = []
        self._table_row_idx = 0
        self._row_cells: list[tuple[str, int, int]] = []
        self._cell_text: list[str] = []
        self._in_cell = False
        self._cell_tag = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        attr_map = dict(attrs)
        classes = attr_map.get("class", "")
        class_set = set(classes.split()) if classes else set()

        if tag in {"h2", "h3"} and (
            "section-heading" in class_set or "catalog-subheading" in class_set
        ):
            self._in_heading = True
            self._heading_tag = tag
            self._heading_text = []

        if tag == "table" and "catalog-table" in class_set:
            self._in_table = True
            self._grid = []
            self._table_row_idx = 0
            self._in_thead = False

        if self._in_table and tag == "thead":
            self._in_thead = True

        if self._in_table and tag == "tbody":
            self._in_thead = False

        if self._in_table and tag == "tr":
            self._row_cells = []

        if self._in_table and tag in {"th", "td"}:
            self._in_cell = True
            self._cell_tag = tag
            self._cell_text = []
            colspan = int(attr_map.get("colspan", "1"))
            rowspan = int(attr_map.get("rowspan", "1"))
            self._row_cells.append((self._cell_tag, colspan, rowspan))

    def handle_endtag(self, tag: str) -> None:
        if self._in_heading and tag == self._heading_tag:
            self._in_heading = False
            heading = clean("".join(self._heading_text))
            if heading:
                self.current_heading = heading

        if self._in_table and tag in {"th", "td"} and self._in_cell:
            self._in_cell = False
            value = clean("".join(self._cell_text))
            tag_name, colspan, rowspan = self._row_cells[-1]
            self._row_cells[-1] = (tag_name, colspan, rowspan, value)

        if self._in_table and tag == "tr" and self._row_cells:
            self._place_row(self._table_row_idx, self._row_cells)
            self._table_row_idx += 1
            self._row_cells = []

        if self._in_table and tag == "table":
            self._in_table = False
            rows = self._finalize_grid()
            if len(rows) > 1 and self.current_heading:
                self.blocks.append((self.current_heading, rows))

    def handle_data(self, data: str) -> None:
        if self._in_heading:
            self._heading_text.append(data)
        if self._in_cell:
            self._cell_text.append(data)

    def _place_row(self, row_idx: int, cells: list) -> None:
        while len(self._grid) <= row_idx:
            self._grid.append([])

        col_idx = 0
        for _tag, colspan, rowspan, value in cells:
            while (
                col_idx < len(self._grid[row_idx])
                and self._grid[row_idx][col_idx] is not None
            ):
                col_idx += 1

            for r in range(row_idx, row_idx + rowspan):
                while len(self._grid) <= r:
                    self._grid.append([])
                while len(self._grid[r]) < col_idx + colspan:
                    self._grid[r].append(None)

                for c in range(col_idx, col_idx + colspan):
                    if r == row_idx:
                        self._grid[r][c] = value if c == col_idx else None
                    else:
                        self._grid[r][c] = _CELL_SKIP

            col_idx += colspan

    def _finalize_grid(self) -> list[list[str]]:
        if not self._grid:
            return []

        max_cols = max(len(row) for row in self._grid)
        grid = [row + [""] * (max_cols - len(row)) for row in self._grid]
        grid = [
            ["" if cell in (None, _CELL_SKIP) else cell for cell in row]
            for row in grid
        ]

        header_idx = 1
        while header_idx < len(grid) and not any(grid[header_idx]):
            header_idx += 1

        if header_idx < len(grid) and self._is_two_row_header(grid[header_idx]):
            merged = self._merge_header_rows(grid[0], grid[header_idx])
            tail = grid[header_idx + 1 :]
            while tail and not any(tail[0]):
                tail = tail[1:]
            return [merged] + tail

        return grid

    @staticmethod
    def _is_two_row_header(second_row: list[str]) -> bool:
        joined = " ".join(second_row).lower()
        return "опт" in joined or "роздріб" in joined

    @staticmethod
    def _merge_header_rows(top_row: list[str], bottom_row: list[str]) -> list[str]:
        merged: list[str] = []
        parent = ""
        for top, bottom in zip(top_row, bottom_row):
            if top:
                parent = top
            group = top or parent
            if bottom:
                merged.append(f"{group} · {bottom}" if group else bottom)
            else:
                merged.append(group)
        return merged


def cell_paragraph(text: str, *, header: bool = False, align=TA_CENTER) -> Paragraph:
    style = ParagraphStyle(
        "Cell",
        fontName="Arial-Bold" if header else "Arial",
        fontSize=7 if header else 7.5,
        leading=9,
        alignment=align,
        textColor=colors.HexColor("#0F172A"),
        wordWrap="CJK",
    )
    safe = (text or "—").replace("&", "&amp;")
    return Paragraph(safe, style)


def table_to_flowable(data: list[list[str]], available_width: float) -> Table:
    header = [cell_paragraph(v, header=True, align=TA_LEFT if i == 0 else TA_CENTER) for i, v in enumerate(data[0])]
    body = [
        [
            cell_paragraph(
                row[i],
                align=TA_LEFT if i == 0 else TA_CENTER,
            )
            for i in range(len(data[0]))
        ]
        for row in data[1:]
    ]
    flow_data = [header] + body

    col_count = len(data[0])
    if col_count == 1:
        widths = [available_width]
    elif col_count == 2:
        widths = [available_width * 0.62, available_width * 0.38]
    elif col_count == 3:
        widths = [available_width * 0.42, available_width * 0.29, available_width * 0.29]
    else:
        first = min(22 * mm, available_width * 0.1)
        rest = (available_width - first) / (col_count - 1)
        widths = [first] + [rest] * (col_count - 1)

    table = Table(flow_data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF9")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def build_pdf() -> None:
    pdfmetrics.registerFont(TTFont("Arial", FONT_REGULAR))
    pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_BOLD))

    parser = CatalogParser()
    parser.feed(CATALOG_HTML.read_text(encoding="utf-8"))
    blocks = parser.blocks

    portrait = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )
    landscape_doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=landscape(A4),
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PriceTitle",
        parent=styles["Title"],
        fontName="Arial-Bold",
        fontSize=17,
        leading=21,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0F172A"),
    )
    body_style = ParagraphStyle(
        "PriceBody",
        parent=styles["BodyText"],
        fontName="Arial",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading3"],
        fontName="Arial-Bold",
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=4,
        spaceAfter=3,
    )

    def make_story(doc: SimpleDocTemplate) -> list:
        story = [
            Paragraph("ПРАЙС-ЛИСТ ВОДОВІТРОДИМ", title_style),
            Spacer(1, 2 * mm),
            Paragraph("Оцинковка: 0,42 мм · Ціни в грн", body_style),
            Paragraph("Оптові замовлення: від 5000 грн", body_style),
            Paragraph(f"Контакти: {' · '.join(CONTACTS)}", body_style),
            Spacer(1, 3 * mm),
        ]

        for i, (title, data) in enumerate(blocks):
            story.append(Paragraph(title, heading_style))
            story.append(table_to_flowable(data, doc.width))
            if i < len(blocks) - 1:
                story.append(Spacer(1, 3 * mm))
        story.append(
            Spacer(1, 2 * mm),
        )
        story.append(
            Paragraph(
                "Для уточнення залишків і термінів виготовлення телефонуйте менеджеру.",
                body_style,
            )
        )
        return story

    # Широка таблиця труб (7 колонок) — альбомна орієнтація всього PDF
    needs_landscape = any(len(rows[0]) >= 6 for _, rows in blocks)
    doc = landscape_doc if needs_landscape else portrait
    doc.build(make_story(doc))
    print(f"PDF created: {OUTPUT_PDF} ({'landscape' if needs_landscape else 'portrait'})")


if __name__ == "__main__":
    build_pdf()
