# Wraps scripts/page.html in a full HTML document -> index.html
import pathlib
root = pathlib.Path(__file__).resolve().parent.parent
body = (root / "scripts" / "page.html").read_text(encoding="utf8")
head = ('<!doctype html><html lang="vi"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<style>:root{color-scheme:light}body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>'
        '</head><body>')
(root / "index.html").write_text(head + body + "</body></html>", encoding="utf8")
