"""Build a Word file of the proposed chapter 6 changes as tracked insertions (no text from the book).

Usage: python ch6_track_changes.py <ch6.yml> <out.docx>
Each passage: a plain heading (page, section, verdict) and the paraphrased message, then the draft
paragraph as a tracked insertion, with the references in a Word comment.
"""
import re
import sys
import datetime as dt
import yaml
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

AUTHOR = "Veille automatisée (LLM)"
NOW = dt.datetime(2026, 11, 23, 12, 0, 0).strftime("%Y-%m-%dT%H:%M:%SZ")
VERDICT = {"tient": "Tient", "renforcé": "Renforcé", "nuancé": "Nuancé", "contredit": "Contredit", "nouveau": "Nouvelle section"}

src, out = sys.argv[1], sys.argv[2]
passages = yaml.safe_load(open(src, encoding="utf-8"))

doc = Document()
st = doc.styles["Normal"]
st.font.name = "Calibri"
st.font.size = Pt(11)

doc.add_heading("Chapitre 6 · La productivité : modifications proposées (mode suivi)", level=1)
intro = doc.add_paragraph()
intro.add_run(
    "Version du 23 novembre 2026, tirée du site de veille (politiques-eco-epreuve-des-faits.github.io/chapitre-6). "
    "Chaque brouillon de paragraphe apparaît comme une insertion suivie, à accepter ou refuser dans Word "
    "(Révision > Accepter / Refuser), avec ses références en commentaire. Le fichier ne reproduit aucun texte du manuel : "
    "chaque insertion est repérée par sa page, sa section et un résumé du message concerné. "
    "Avec la version Word du chapitre, les mêmes insertions pourront être placées directement dans le texte."
).italic = True

_id = [100]


def next_id():
    _id[0] += 1
    return str(_id[0])


def md_runs(par, text):
    """Add runs for **bold** and *italic* markdown, return the runs."""
    runs = []
    for tok in re.split(r"(\*\*.+?\*\*|\*.+?\*)", text):
        if not tok:
            continue
        if tok.startswith("**"):
            r = par.add_run(tok[2:-2]); r.bold = True
        elif tok.startswith("*"):
            r = par.add_run(tok[1:-1]); r.italic = True
        else:
            r = par.add_run(tok)
        runs.append(r)
    return runs


def track_insert(par, runs):
    """Wrap runs in a <w:ins> element so Word shows them as tracked insertions."""
    ins = OxmlElement("w:ins")
    ins.set(qn("w:id"), next_id())
    ins.set(qn("w:author"), AUTHOR)
    ins.set(qn("w:date"), NOW)
    first = runs[0]._r
    first.addprevious(ins)
    for r in runs:
        ins.append(r._r)
    # mark the paragraph mark as inserted too, so rejecting removes the whole paragraph
    ppr = par._p.get_or_add_pPr()
    rpr = ppr.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr"); ppr.append(rpr)
    pins = OxmlElement("w:ins")
    pins.set(qn("w:id"), next_id()); pins.set(qn("w:author"), AUTHOR); pins.set(qn("w:date"), NOW)
    rpr.append(pins)


for p in passages:
    h = doc.add_paragraph()
    r = h.add_run(f"{p['page']} · {p['section']} · {VERDICT.get(p['verdict'], p['verdict'])}")
    r.bold = True
    r.font.color.rgb = RGBColor(0x2A, 0x4D, 0x8F)
    h.paragraph_format.space_before = Pt(14)

    m = doc.add_paragraph()
    lab = m.add_run("Message du livre (résumé, pas le texte) : "); lab.italic = True
    mr = m.add_run(str(p["message"]).strip()); mr.italic = True
    for x in (lab, mr):
        x.font.color.rgb = RGBColor(0x6B, 0x73, 0x85)

    where = "Nouvelle section à insérer à cet endroit." if p["verdict"] == "nouveau" else (
        "Paragraphe à insérer après le passage concerné ; il corrige le chiffre du livre." if p["verdict"] == "contredit"
        else "Paragraphe à insérer après le passage concerné.")
    w = doc.add_paragraph(); wr = w.add_run(where); wr.font.size = Pt(9); wr.font.color.rgb = RGBColor(0x6B, 0x73, 0x85)

    body = str(p["brouillon"]).strip()
    for i, chunk in enumerate([c for c in body.split("\n\n") if c.strip()]):
        par = doc.add_paragraph()
        runs = md_runs(par, chunk.strip())
        if i == 0:
            refs = p.get("references") or []
            note = ("Références à ajouter :\n" + "\n".join("- " + re.sub(r"\*", "", x) for x in refs)) if refs else "Pas de nouvelle référence."
            doc.add_comment(runs, text=note + f"\n(Passage {p['id']}, vérifié le {p.get('maj_le', '')})", author=AUTHOR, initials="VA")
        track_insert(par, runs)

doc.save(out)
print("wrote", out, len(passages), "passages")
