#!/usr/bin/env python3
"""Minify CSS; split catalog-only rules into catalog.css. Run: python3 tools/build_assets.py"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_START = "/* ——— Catalog page ——— */"
CATALOG_END = "/* ——— Why + Steps ——— */"


def minify_css(text: str) -> str:
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{}:;,>+~])\s*", r"\1", text)
    return text.strip()


def split_catalog_once() -> None:
    path = ROOT / "styles.css"
    text = path.read_text(encoding="utf-8")
    if CATALOG_START not in text:
        print("catalog block already split, skip")
        return
    start = text.index(CATALOG_START)
    end = text.index(CATALOG_END)
    catalog = text[start:end].strip() + "\n"
    base = (text[:start] + text[end:]).strip() + "\n"
    path.write_text(base, encoding="utf-8")
    (ROOT / "catalog.css").write_text(catalog, encoding="utf-8")
    print(f"split catalog.css ({len(catalog)} bytes)")


def minify_js(text: str) -> str:
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    text = re.sub(r"(^|[^:])//.*", r"\1", text, flags=re.M)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{}();,=+\-*/<>])\s*", r"\1", text)
    return text.strip()


def minify_all() -> None:
    for path in sorted(ROOT.glob("*.css")):
        if path.name.endswith(".min.css"):
            continue
        src = path.read_text(encoding="utf-8")
        mini = minify_css(src)
        out = path.with_name(path.stem + ".min.css")
        out.write_text(mini + "\n", encoding="utf-8")
        print(f"{path.name}: {len(src)} -> {len(mini)} ({out.name})")

    js = ROOT / "analytics.js"
    if js.exists():
        src = js.read_text(encoding="utf-8")
        mini = minify_js(src)
        (ROOT / "analytics.min.js").write_text(mini + "\n", encoding="utf-8")
        print(f"analytics.js: {len(src)} -> {len(mini)} (analytics.min.js)")


if __name__ == "__main__":
    split_catalog_once()
    minify_all()
