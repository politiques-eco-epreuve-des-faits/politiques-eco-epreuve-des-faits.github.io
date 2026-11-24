"""Weekly academic sweep for the monthly routine (all chapters).

Saves every new item from fixed sources into routines/flux.json, so that the monthly
routine sees a full month even though the feeds only go back one or two weeks:
- NBER working papers (RSS, latest week), with abstracts
- CEPR discussion papers (RSS, about two weeks), with abstracts and programme area
- Articles in 8 journals via Crossref (registered in Crossref in the last 60 days): AER, Econometrica, QJE, JPE,
  REStud, JEL, JEP, Annual Review of Economics (abstracts when Crossref has them)

No screening here: the routine reads titles and abstracts against each chapter's messages.
Items older than 180 days are dropped. Standard library only.
"""
import datetime as dt
import json
import pathlib
import re
import time
import urllib.request
import xml.etree.ElementTree as ET

OUT = pathlib.Path(__file__).resolve().parent.parent / "routines" / "flux.json"
UA = {"User-Agent": "veille-manuel-feeds/1.0"}
JOURNALS = {
    "American Economic Review": "0002-8282",
    "Econometrica": "0012-9682",
    "Quarterly Journal of Economics": "0033-5533",
    "Journal of Political Economy": "0022-3808",
    "Review of Economic Studies": "0034-6527",
    "Journal of Economic Literature": "0022-0515",
    "Journal of Economic Perspectives": "0895-3309",
    "Annual Review of Economics": "1941-1383",
}
TODAY = dt.date.today()


def get(url, tries=3):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(10)


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def nber():
    items = []
    for it in ET.fromstring(get("https://back.nber.org/rss/new.xml")).iter("item"):
        title, _, authors = (it.findtext("title") or "").partition(" -- by ")
        items.append({"source": "NBER", "date": TODAY.isoformat(), "title": clean(title),
                      "authors": clean(authors), "url": clean(it.findtext("link")),
                      "abstract": clean(it.findtext("description"))})
    return items


def cepr():
    ns = {"dc": "http://purl.org/dc/elements/1.1/", "cepr": "https://cepr.org/rss/ns/1.0"}
    items = []
    for it in ET.fromstring(get("https://cepr.org/rss/discussion-paper")).iter("item"):
        pub = it.findtext("pubDate") or ""
        try:
            date = dt.datetime.strptime(pub[:16], "%a, %d %b %Y").date().isoformat()
        except ValueError:
            date = TODAY.isoformat()
        items.append({"source": "CEPR", "date": date, "title": clean(it.findtext("title")),
                      "authors": clean(it.findtext("dc:creator", namespaces=ns)),
                      "url": clean(it.findtext("link")),
                      "programme": clean(it.findtext("cepr:programme_areas", namespaces=ns)),
                      "abstract": clean(it.findtext("description"))})
    return items


def journals():
    """One small page (40 rows) at a time: large Crossref responses get cut off."""
    since = (TODAY - dt.timedelta(days=60)).isoformat()
    items = []
    for name, issn in JOURNALS.items():
        offset = 0
        while True:
            url = (f"https://api.crossref.org/journals/{issn}/works?filter=from-created-date:{since},"
                   f"type:journal-article&rows=40&offset={offset}&select=title,author,issued,DOI,abstract")
            batch = json.loads(get(url))["message"]["items"]
            for w in batch:
                parts = w.get("issued", {}).get("date-parts", [[None]])[0]
                date = "-".join(f"{p:02d}" if i else str(p) for i, p in enumerate(parts) if p)
                authors = ", ".join(f"{a.get('given', '')} {a.get('family', '')}".strip()
                                    for a in w.get("author", []))
                items.append({"source": name, "date": date,
                              "title": clean((w.get("title") or [""])[0]), "authors": authors,
                              "url": f"https://doi.org/{w['DOI']}", "abstract": clean(w.get("abstract"))})
            if len(batch) < 40 or offset >= 400:
                break
            offset += 40
    return items


def main():
    old = json.loads(OUT.read_text()) if OUT.exists() else []
    seen = {i["url"] for i in old}
    new, errors = [], []
    for fetch in (nber, cepr, journals):
        try:
            for i in fetch():
                if i["url"] and i["url"] not in seen:
                    i["collecte"] = TODAY.isoformat()
                    new.append(i)
                    seen.add(i["url"])
        except Exception as e:  # one source down must not block the others
            errors.append(f"{fetch.__name__}: {e}")
    cutoff = (TODAY - dt.timedelta(days=180)).isoformat()
    keep = [i for i in old + new if i.get("collecte", i["date"]) >= cutoff]
    keep.sort(key=lambda i: (i["collecte"], i["source"]), reverse=True)
    OUT.write_text(json.dumps(keep, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(new)} new items, {len(keep)} kept")
    for e in errors:
        print("ERROR", e)
    if errors and not new:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
