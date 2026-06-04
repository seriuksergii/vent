#!/usr/bin/env python3
import re
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "webfonts"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Manrope:wght@400;600;700&family=Unbounded:wght@700;800&display=swap"
)

req = urllib.request.Request(URL, headers={"User-Agent": UA})
css = urllib.request.urlopen(req).read().decode()
blocks = re.findall(
    r"/\*\s*(cyrillic|latin)\s*\*/\s*@font-face\s*\{([^}]+)\}",
    css,
    re.DOTALL,
)

OUT.mkdir(exist_ok=True)
face_lines = []

for subset, body in blocks:
    fam = re.search(r"font-family:\s*'([^']+)'", body).group(1)
    weight = re.search(r"font-weight:\s*(\d+)", body).group(1)
    uni = re.search(r"unicode-range:\s*([^;]+);", body).group(1).strip()
    url = re.search(r"url\((https://[^)]+\.woff2)\)", body).group(1)
    name = f"{fam.lower()}-{weight}-{subset}.woff2"
    dest = OUT / name
    if not dest.exists() or dest.stat().st_size == 0:
        subprocess.run(["curl", "-fsSL", "-o", str(dest), url], check=True)
    face_lines.append(
        f"@font-face {{\n"
        f"  font-family: '{fam}';\n"
        f"  font-style: normal;\n"
        f"  font-weight: {weight};\n"
        f"  font-display: swap;\n"
        f"  src: url('webfonts/{name}') format('woff2');\n"
        f"  unicode-range: {uni};\n"
        f"}}"
    )

(ROOT / "fonts.css").write_text("\n".join(face_lines) + "\n", encoding="utf-8")
print(f"fonts.css: {len(face_lines)} @font-face rules")
