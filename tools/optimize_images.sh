#!/usr/bin/env bash
# Regenerate WebP assets for PageSpeed (run from repo root).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/tools/source-images"
OUT="$ROOT/images"
mkdir -p "$OUT" "$SRC"

resize_webp() {
  local src="$1" width="$2" out="$3"
  cwebp -quiet -q 82 -resize "$width" 0 "$src" -o "$out"
}

# Hero (LCP): 600w mobile, 900w desktop
resize_webp "$SRC/hero_img.png" 600 "$OUT/hero-600.webp"
resize_webp "$SRC/hero_img.png" 900 "$OUT/hero-900.webp"

# Product cards & catalog thumbs (~320px display → 640w)
for n in 00 11 22 33 44 55 66 77 88 99 100 110; do
  if [ -f "$SRC/${n}.png" ]; then
    resize_webp "$SRC/${n}.png" 640 "$OUT/${n}-640.webp"
  fi
done

# Catalog large single photos (max 380px → 760w)
for n in 00 11 22 33 44 55 99 100 110; do
  if [ -f "$SRC/${n}.png" ]; then
    resize_webp "$SRC/${n}.png" 760 "$OUT/${n}-760.webp"
  fi
done

echo "Done. Output in images/"
ls -lh "$OUT"
