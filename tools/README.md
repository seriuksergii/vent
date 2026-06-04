# Скрипти розробки (не потрібні на хостингу)

| Файл | Коли запускати |
|------|----------------|
| `build_assets.py` | Після змін у `styles.css`, `critical.css`, `catalog.css`, `icons.css`, `fonts.css`, `analytics.js` — збирає `*.min.css` / `analytics.min.js` |
| `optimize_images.sh` | Після заміни PNG у `source-images/` — збирає WebP у `../images/` |
| `_download_fonts.py` | Після зміни набору шрифтів — `python3 tools/_download_fonts.py` |
| `build_price_pdf.py` | Після зміни таблиць у `catalog.html` — оновлює `../price.pdf` |

На сервер завантажуйте лише корінь сайту без папки `tools/`.
