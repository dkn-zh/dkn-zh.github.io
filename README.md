# danielknuchel.ch

Persönliche Website, statisch generiert mit einem kleinen Python-Skript und auf GitHub Pages veröffentlicht.

## Lokal arbeiten

```bash
pip install -r requirements.txt
python3 build.py --serve      # baut nach dist/ und öffnet http://localhost:8000
```

## Wo was liegt

| Ort | Inhalt |
|---|---|
| `config.yaml` | Name, URL, Domain, Profil-Links, alle Oberflächentexte in DE und EN |
| `content/de/*.md`, `content/en/*.md` | Eine Datei pro Seite. Oben YAML-Frontmatter (Titel, Navigation, Template), darunter Markdown. |
| `data/publications.yaml` | Publikationen, eine Liste. Neue Einträge oben anfügen. |
| `data/talks.yaml` | Vorträge, Poster, Workshops, Organisation, Outreach. |
| `data/courses.yaml` | Lehrveranstaltungen. Ein Kurs kann `summary:` (Markdown) und `readings:` (Liste) haben; dann wird er auf der Lehre-Seite aufklappbar. |
| `templates/` | HTML-Gerüst (Jinja2). |
| `static/` | CSS, Bilder, PDFs. Wird unverändert kopiert. |

## Neue Publikation eintragen

1. Eintrag in `data/publications.yaml` ergänzen (Vorlage: bestehender Eintrag; `status` weglassen, wenn erschienen).
2. `python3 build.py` lokal prüfen.
3. `git commit` und `git push`. GitHub Actions baut und veröffentlicht automatisch.

Reihenfolge bei neuen Publikationen: zuerst ORCID, dann hier, dann Institutsseite.

## Veröffentlichen

Repository `<github-name>.github.io`, Branch `main`. In den Repository-Einstellungen unter *Pages* die Quelle auf *GitHub Actions* stellen. Für die eigene Domain `domain:` in `config.yaml` setzen und beim Domain-Anbieter einen CNAME-Eintrag auf `<github-name>.github.io` anlegen.
