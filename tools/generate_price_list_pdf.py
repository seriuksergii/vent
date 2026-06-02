from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


SOURCE_XLS = Path("/Users/sergejserduk/Desktop/прайс жестянка.xls")
OUTPUT_PDF = Path("/Users/sergejserduk/Desktop/VENT LAND/Vent/price-list-zhestyanka-ukr.pdf")
OUTPUT_XLSX = Path("/Users/sergejserduk/Desktop/VENT LAND/Vent/price-list-zhestyanka-ukr.xlsx")

FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def _parse_number_or_range(text: str) -> tuple[int | None, int | None]:
    t = normalize_text(text).replace(" ", "")
    if not t:
        return (None, None)
    if "-" in t:
        left, right = t.split("-", 1)
        if left.isdigit() and right.isdigit():
            return (int(left), int(right))
        return (None, None)
    try:
        num = float(t.replace(",", "."))
        return (int(round(num)), None)
    except ValueError:
        return (None, None)


def to_opt_price_text(value: Any) -> str:
    text = normalize_text(value).replace(" ", "")
    if not text:
        return ""

    a, b = _parse_number_or_range(text)
    if a is None and b is None:
        return normalize_text(value)
    if b is not None:
        return f"{a}-{b} грн"
    return f"{a} грн"


def to_retail_price_text(value: Any) -> str:
    text = normalize_text(value).replace(" ", "")
    if not text:
        return ""

    a, b = _parse_number_or_range(text)
    if a is None and b is None:
        return ""
    if b is not None:
        ra = int(round(a * 1.1))
        rb = int(round(b * 1.1))
        return f"{ra}-{rb} грн"
    return f"{int(round(a * 1.1))} грн"


def translate_name(name: str) -> str:
    mapping = {
        "Хомут (крепление трубы  Ø 100 - 150)": "Хомут (кріплення труби Ø 100-150)",
        "Хомут шпилька  (Ø 100 - 150)": "Хомут-шпилька (Ø 100-150)",
        "Зонт двойной 1 шт.": "Подвійний зонт, 1 шт.",
        "Переходник 1 шт.": "Перехідник, 1 шт.",
        "Дефлектор (100 - 150)": "Дефлектор (100-150)",
        "Шибер (100 - 150)": "Шибер (100-150)",
        "Соединение гофры (100-150)": "З'єднання гофри (100-150)",
        "Желоб 2 метра (диаметр 120 мм.)": "Жолоб 2 метри (діаметр 120 мм)",
        "Ливнеприёмник с патрубком": "Дощоприймач з патрубком",
        "Поворот желоба (диаметр 120 мм.)": "Поворот жолоба (діаметр 120 мм)",
        "Крепление желоба": "Кріплення жолоба",
        "Заглушка желоба": "Заглушка жолоба",
        "Конек 2 метр (125*125 мм.)": "Коник 2 м (125x125 мм)",
        "Конек 2 метр (150*150 мм.)": "Коник 2 м (150x150 мм)",
        "Конек 2 метр (165*165 мм.)": "Коник 2 м (165x165 мм)",
        "Конек 2 метр (200*200 мм.)": "Коник 2 м (200x200 мм)",
        "Конек 2 метр (250*250 мм.)": "Коник 2 м (250x250 мм)",
    }

    clean = normalize_text(name).replace("*", "x")
    if clean.startswith("Отлив на подоконник"):
        return clean.replace("Отлив на подоконник", "Відлив на підвіконня")
    return mapping.get(clean, clean)


def build_main_table(df: pd.DataFrame) -> list[list[str]]:
    columns = [
        "Діаметр, мм",
        "Труба 1 м",
        "Труба 0,5 м",
        "Труба 0,25 м",
        "Відвід 90°",
        "Трійник із загл.",
        "Зонт",
        "Коліно 45°",
        "Воронка",
        "Флюгер",
    ]

    data: list[list[str]] = [columns]
    for row_idx in range(8, 26):
        row = df.iloc[row_idx]
        diameter = normalize_text(row[0])
        if not diameter:
            continue

        line = [diameter]
        for col_idx in range(1, 10):
            raw = row[col_idx]
            opt = to_opt_price_text(raw)
            retail = to_retail_price_text(raw)
            if opt and retail:
                line.append(f"Опт: {opt}\nРоздріб: {retail}")
            else:
                line.append("")
        data.append(line)
    return data


def build_extra_table(df: pd.DataFrame) -> list[list[str]]:
    data = [["Найменування", "Опт", "Роздріб"]]
    for row_idx in range(26, len(df)):
        name = normalize_text(df.iloc[row_idx, 0])
        raw_price = df.iloc[row_idx, 1]
        if not name:
            continue

        item_name = translate_name(name)
        opt = to_opt_price_text(raw_price)
        retail = to_retail_price_text(raw_price)
        if not opt:
            opt = "Уточнюйте"
        if not retail:
            retail = "Уточнюйте"
        data.append([item_name, opt, retail])
    return data


def build_main_df_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    base_cols = [
        "Труба 1 м",
        "Труба 0,5 м",
        "Труба 0,25 м",
        "Відвід 90°",
        "Трійник із загл.",
        "Зонт",
        "Коліно 45°",
        "Воронка",
        "Флюгер",
    ]

    rows: list[dict[str, str]] = []
    for row_idx in range(8, 26):
        row = df.iloc[row_idx]
        diameter = normalize_text(row[0])
        if not diameter:
            continue

        out: dict[str, str] = {"Діаметр, мм": diameter}
        for i, title in enumerate(base_cols, start=1):
            raw = row[i]
            out[f"{title} — Опт"] = to_opt_price_text(raw)
            out[f"{title} — Роздріб"] = to_retail_price_text(raw)
        rows.append(out)

    columns = ["Діаметр, мм"]
    for title in base_cols:
        columns.extend([f"{title} — Опт", f"{title} — Роздріб"])
    return pd.DataFrame(rows, columns=columns)


def build_extra_df_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for row_idx in range(26, len(df)):
        name = normalize_text(df.iloc[row_idx, 0])
        raw_price = df.iloc[row_idx, 1]
        if not name:
            continue

        rows.append(
            {
                "Найменування": translate_name(name),
                "Опт": to_opt_price_text(raw_price) or "Уточнюйте",
                "Роздріб": to_retail_price_text(raw_price) or "Уточнюйте",
            }
        )
    return pd.DataFrame(rows, columns=["Найменування", "Опт", "Роздріб"])


def table_style(header_bg: colors.Color) -> TableStyle:
    return TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), "Arial"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )


def write_excel(df_source: pd.DataFrame) -> None:
    main_df = build_main_df_for_excel(df_source)
    extra_df = build_extra_df_for_excel(df_source)

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        main_df.to_excel(writer, index=False, sheet_name="Труби та елементи")
        extra_df.to_excel(writer, index=False, sheet_name="Додаткові вироби")

        note_df = pd.DataFrame(
            [
                {
                    "Пояснення": "Опт — ціни при замовленні від 5000 грн.",
                    "Примітка": "Роздріб — +10% до оптової ціни.",
                }
            ]
        )
        note_df.to_excel(writer, index=False, sheet_name="Примітки")


def main() -> None:
    pdfmetrics.registerFont(TTFont("Arial", FONT_REGULAR))
    pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_BOLD))

    df = pd.read_excel(SOURCE_XLS, sheet_name="Лист1", header=None)

    # Excel export: розбиття ціни на Опт/Роздріб
    write_excel(df)

    main_data = build_main_table(df)
    extra_data = build_extra_table(df)

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title",
        parent=styles["Title"],
        fontName="Arial-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "subtitle",
        parent=styles["BodyText"],
        fontName="Arial",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        alignment=1,
    )
    note_style = ParagraphStyle(
        "note",
        parent=styles["BodyText"],
        fontName="Arial",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
    )

    content = [
        Paragraph("ПРАЙС-ЛИСТ ЖЕСТЯНИХ ВИРОБІВ (оцинковка 0,42 мм)", title_style),
        Spacer(1, 5 * mm),
        Paragraph("Ціни вказані у гривнях.", subtitle_style),
        Paragraph("Опт: від 5000 грн. Роздріб: +10% до оптової ціни.", subtitle_style),
        Spacer(1, 5 * mm),
        Paragraph("Труби та елементи за діаметром", ParagraphStyle("h", parent=subtitle_style, fontName="Arial-Bold")),
        Spacer(1, 2 * mm),
    ]

    main_col_widths = [20 * mm, 24 * mm, 24 * mm, 24 * mm, 24 * mm, 30 * mm, 20 * mm, 24 * mm, 24 * mm, 24 * mm]
    main_table = Table(main_data, colWidths=main_col_widths, repeatRows=1)
    main_table.setStyle(table_style(colors.HexColor("#2563EB")))
    content.append(main_table)

    content.extend(
        [
            Spacer(1, 6 * mm),
            Paragraph("Додаткові вироби", ParagraphStyle("h2", parent=subtitle_style, fontName="Arial-Bold")),
            Spacer(1, 2 * mm),
        ]
    )

    extra_col_widths = [160 * mm, 45 * mm, 45 * mm]
    extra_table = Table(extra_data, colWidths=extra_col_widths, repeatRows=1)
    extra_table.setStyle(table_style(colors.HexColor("#0EA5E9")))
    extra_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (0, -1), 6),
            ]
        )
    )
    content.append(extra_table)
    content.extend(
        [
            Spacer(1, 4 * mm),
            Paragraph("Ціни позначені явно: «Опт» та «Роздріб», щоб клієнт одразу бачив тип ціни.", note_style),
        ]
    )

    doc.build(content)
    print(f"PDF created: {OUTPUT_PDF}")
    print(f"XLSX created: {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


SOURCE_XLS = Path("/Users/sergejserduk/Desktop/прайс жестянка.xls")
OUTPUT_PDF = Path("/Users/sergejserduk/Desktop/VENT LAND/Vent/price-list-zhestyanka-ukr.pdf")
OUTPUT_XLSX = Path("/Users/sergejserduk/Desktop/VENT LAND/Vent/price-list-zhestyanka-ukr.xlsx")

FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def _parse_number_or_range(text: str) -> tuple[int | None, int | None]:
    t = normalize_text(text).replace(" ", "")
    if not t:
        return (None, None)
    if "-" in t:
        left, right = t.split("-", 1)
        if left.isdigit() and right.isdigit():
            return (int(left), int(right))
        return (None, None)
    try:
        num = float(t.replace(",", "."))
        return (int(round(num)), None)
    except ValueError:
        return (None, None)


def to_opt_price_text(value: Any) -> str:
    text = normalize_text(value).replace(" ", "")
    if not text:
        return ""

    a, b = _parse_number_or_range(text)
    if a is None and b is None:
        return normalize_text(value)
    if b is not None:
        return f"{a}-{b} грн"
    return f"{a} грн"


def to_retail_price_text(value: Any) -> str:
    text = normalize_text(value).replace(" ", "")
    if not text:
        return ""

    a, b = _parse_number_or_range(text)
    if a is None and b is None:
        return ""
    if b is not None:
        ra = int(round(a * 1.1))
        rb = int(round(b * 1.1))
        return f"{ra}-{rb} грн"
    return f"{int(round(a * 1.1))} грн"


def translate_name(name: str) -> str:
    mapping = {
        "Хомут (крепление трубы  Ø 100 - 150)": "Хомут (кріплення труби Ø 100-150)",
        "Хомут шпилька  (Ø 100 - 150)": "Хомут-шпилька (Ø 100-150)",
        "Зонт двойной 1 шт.": "Подвійний зонт, 1 шт.",
        "Переходник 1 шт.": "Перехідник, 1 шт.",
        "Дефлектор (100 - 150)": "Дефлектор (100-150)",
        "Шибер (100 - 150)": "Шибер (100-150)",
        "Соединение гофры (100-150)": "З'єднання гофри (100-150)",
        "Желоб 2 метра (диаметр 120 мм.)": "Жолоб 2 метри (діаметр 120 мм)",
        "Ливнеприёмник с патрубком": "Дощоприймач з патрубком",
        "Поворот желоба (диаметр 120 мм.)": "Поворот жолоба (діаметр 120 мм)",
        "Крепление желоба": "Кріплення жолоба",
        "Заглушка желоба": "Заглушка жолоба",
        "Конек 2 метр (125*125 мм.)": "Коник 2 м (125x125 мм)",
        "Конек 2 метр (150*150 мм.)": "Коник 2 м (150x150 мм)",
        "Конек 2 метр (165*165 мм.)": "Коник 2 м (165x165 мм)",
        "Конек 2 метр (200*200 мм.)": "Коник 2 м (200x200 мм)",
        "Конек 2 метр (250*250 мм.)": "Коник 2 м (250x250 мм)",
    }

    clean = normalize_text(name).replace("*", "x")
    if clean.startswith("Отлив на подоконник"):
        return clean.replace("Отлив на подоконник", "Відлив на підвіконня")
    return mapping.get(clean, clean)


def build_main_table(df: pd.DataFrame) -> list[list[str]]:
    columns = [
        "Діаметр, мм",
        "Труба 1 м",
        "Труба 0,5 м",
        "Труба 0,25 м",
        "Відвід 90°",
        "Трійник із загл.",
        "Зонт",
        "Коліно 45°",
        "Воронка",
        "Флюгер",
    ]

    data: list[list[str]] = [columns]
    for row_idx in range(8, 26):
        row = df.iloc[row_idx]
        diameter = normalize_text(row[0])
        if not diameter:
            continue

        line = [diameter]
        for col_idx in range(1, 10):
            raw = row[col_idx]
            opt = to_opt_price_text(raw)
            retail = to_retail_price_text(raw)
            if opt and retail:
                line.append(f"Опт: {opt}\nРоздріб: {retail}")
            else:
                line.append("")
        data.append(line)
    return data


def build_extra_table(df: pd.DataFrame) -> list[list[str]]:
    data = [["Найменування", "Опт", "Роздріб"]]
    for row_idx in range(26, len(df)):
        name = normalize_text(df.iloc[row_idx, 0])
        raw_price = df.iloc[row_idx, 1]
        if not name:
            continue

        item_name = translate_name(name)
        opt = to_opt_price_text(raw_price)
        retail = to_retail_price_text(raw_price)
        if not opt:
            opt = "Уточнюйте"
        if not retail:
            retail = "Уточнюйте"
        data.append([item_name, opt, retail])
    return data


def build_extra_df_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for row_idx in range(26, len(df)):
        name = normalize_text(df.iloc[row_idx, 0])
        raw_price = df.iloc[row_idx, 1]
        if not name:
            continue

        rows.append(
            {
                "Найменування": translate_name(name),
                "Опт": to_opt_price_text(raw_price) or "Уточнюйте",
                "Роздріб": to_retail_price_text(raw_price) or "Уточнюйте",
            }
        )
    return pd.DataFrame(rows, columns=["Найменування", "Опт", "Роздріб"])


def table_style(header_bg: colors.Color) -> TableStyle:
    return TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), "Arial"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )


def write_excel(df_source: pd.DataFrame) -> None:
    extra_df = build_extra_df_for_excel(df_source)
    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        extra_df.to_excel(writer, index=False, sheet_name="Додаткові вироби")

        note_df = pd.DataFrame(
            [
                {
                    "Пояснення": "Опт — ціни при замовленні від 5000 грн.",
                    "Примітка": "Роздріб — +10% до оптової ціни.",
                }
            ]
        )
        note_df.to_excel(writer, index=False, sheet_name="Примітки")


def main() -> None:
    pdfmetrics.registerFont(TTFont("Arial", FONT_REGULAR))
    pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_BOLD))

    df = pd.read_excel(SOURCE_XLS, sheet_name="Лист1", header=None)

    # Excel export: колонка ціни розбита на Опт/Роздріб
    write_excel(df)

    main_data = build_main_table(df)
    extra_data = build_extra_table(df)

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title",
        parent=styles["Title"],
        fontName="Arial-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "subtitle",
        parent=styles["BodyText"],
        fontName="Arial",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        alignment=1,
    )
    note_style = ParagraphStyle(
        "note",
        parent=styles["BodyText"],
        fontName="Arial",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
    )

    content = [
        Paragraph("ПРАЙС-ЛИСТ ЖЕСТЯНИХ ВИРОБІВ (оцинковка 0,42 мм)", title_style),
        Spacer(1, 5 * mm),
        Paragraph("Ціни вказані у гривнях.", subtitle_style),
        Paragraph("Опт: від 5000 грн. Роздріб: +10% до оптової ціни.", subtitle_style),
        Spacer(1, 5 * mm),
        Paragraph("Труби та елементи за діаметром", ParagraphStyle("h", parent=subtitle_style, fontName="Arial-Bold")),
        Spacer(1, 2 * mm),
    ]

    main_col_widths = [20 * mm, 24 * mm, 24 * mm, 24 * mm, 24 * mm, 30 * mm, 20 * mm, 24 * mm, 24 * mm, 24 * mm]
    main_table = Table(main_data, colWidths=main_col_widths, repeatRows=1)
    main_table.setStyle(table_style(colors.HexColor("#2563EB")))
    content.append(main_table)

    content.extend(
        [
            Spacer(1, 6 * mm),
            Paragraph("Додаткові вироби", ParagraphStyle("h2", parent=subtitle_style, fontName="Arial-Bold")),
            Spacer(1, 2 * mm),
        ]
    )

    extra_col_widths = [160 * mm, 45 * mm, 45 * mm]
    extra_table = Table(extra_data, colWidths=extra_col_widths, repeatRows=1)
    extra_table.setStyle(table_style(colors.HexColor("#0EA5E9")))
    extra_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (0, -1), 6),
            ]
        )
    )
    content.append(extra_table)
    content.extend(
        [
            Spacer(1, 4 * mm),
            Paragraph("Ціни позначені явно: «Опт» та «Роздріб», щоб клієнт одразу бачив тип ціни.", note_style),
        ]
    )

    doc.build(content)
    print(f"PDF created: {OUTPUT_PDF}")
    print(f"XLSX created: {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
