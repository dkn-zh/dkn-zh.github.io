#!/usr/bin/env python3
"""Statischer Site-Generator für danielknuchel.ch.

    python3 build.py          baut die Seite nach dist/
    python3 build.py --serve  baut und startet einen lokalen Server auf http://localhost:8000

Struktur:
    config.yaml        Name, URL, Links, Übersetzungen der Oberflächentexte
    content/<lang>/    eine Markdown-Datei pro Seite (YAML-Frontmatter + Text)
    data/*.yaml        Publikationen, Vorträge, Lehrveranstaltungen (sprachunabhängig)
    templates/         Jinja2-Templates
    static/            CSS, Bilder, PDFs (werden 1:1 kopiert)
"""
import argparse
import datetime
import functools
import http.server
import re
import shutil
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)
MD_EXTENSIONS = ["extra", "attr_list", "toc", "sane_lists"]


def load_yaml(path: Path):
    return normalize(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def normalize(obj):
    """YAML liest 2026-12-04 als Datum; wir wollen überall ISO-Strings."""
    if isinstance(obj, dict):
        return {k: normalize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize(v) for v in obj]
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    return obj


def read_page(path: Path):
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER.match(text)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def rel_dir(cfg, lang, slug):
    """Verzeichnis relativ zur Site-Wurzel. Erste Sprache liegt auf /, weitere auf /<lang>/."""
    parts = []
    if lang != cfg["languages"][0]:
        parts.append(lang)
    if slug:
        parts.append(slug)
    return "/".join(parts)


def url_for(cfg, lang, slug):
    d = rel_dir(cfg, lang, slug)
    return "/" if not d else f"/{d}/"


def build():
    cfg = load_yaml(ROOT / "config.yaml")
    data = {p.stem: load_yaml(p) for p in sorted((ROOT / "data").glob("*.yaml"))}
    for inst in data.get("courses", {}).get("institutions", []):
        for c in inst["courses"]:
            c["year"] = re.search(r"(\d{4})(?!.*\d{4})", str(c["sem"])).group(1)  # letztes Jahr im Semesterstring
    today = datetime.date.today()

    env = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals.update(cfg=cfg, data=data, build_date=today)
    env.filters["md"] = lambda s: markdown.markdown(s or "", extensions=["extra"])
    env.filters["md_inline"] = lambda s: re.sub(r"^<p>|</p>$", "", markdown.markdown(s or "", extensions=["extra"]).strip())

    pages = {}
    for lang in cfg["languages"]:
        for path in sorted((ROOT / "content" / lang).glob("*.md")):
            meta, body = read_page(path)
            slug = meta.get("slug", "" if path.stem == "index" else path.stem)
            md = markdown.Markdown(extensions=MD_EXTENSIONS)
            meta.update(slug=slug, lang=lang, html=md.convert(body), url=url_for(cfg, lang, slug))
            pages[(lang, slug)] = meta

    for (lang, slug), page in pages.items():
        other = next(l for l in cfg["languages"] if l != lang)
        alt = page.get("alt", slug)
        page["alt_lang"] = other
        page["alt_url"] = url_for(cfg, other, alt) if (other, alt) in pages else url_for(cfg, other, "")

    nav = {
        lang: sorted((p for (l, _), p in pages.items() if l == lang and p.get("nav")), key=lambda p: p["nav"])
        for lang in cfg["languages"]
    }

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT / "static", DIST / "static")

    for (lang, slug), page in pages.items():
        template = env.get_template(f"{page.get('template', 'page')}.html")
        html = template.render(page=page, nav=nav[lang], lang=lang, t=cfg["strings"][lang], home_url=url_for(cfg, lang, ""))
        out = DIST / rel_dir(cfg, lang, slug) / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")

    first = cfg["languages"][0]
    not_found = env.get_template("404.html").render(page=pages[(first, "")], nav=nav[first], lang=first, t=cfg["strings"][first], home_url="/")
    (DIST / "404.html").write_text(not_found, encoding="utf-8")

    urls = "".join(f"  <url><loc>{cfg['url']}{p['url']}</loc><lastmod>{today}</lastmod></url>\n" for p in pages.values())
    (DIST / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {cfg['url']}/sitemap.xml\n", encoding="utf-8")
    (DIST / ".nojekyll").write_text("")
    if cfg.get("domain"):
        (DIST / "CNAME").write_text(cfg["domain"] + "\n")

    print(f"{len(pages)} Seiten gebaut nach {DIST}")


def serve(port=8000):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
    print(f"http://localhost:{port}  (Ctrl+C beendet)")
    http.server.ThreadingHTTPServer(("", port), handler).serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    build()
    if args.serve:
        serve(args.port)
