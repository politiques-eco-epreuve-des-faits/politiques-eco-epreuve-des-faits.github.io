"""Weekly academic sweep for the monthly routine (all chapters).

Saves every new item from fixed sources into routines/flux.json, looking back 60 days each
time, so that a source that fails one Monday is caught up the next:
- NBER working papers, via Crossref (DOI prefix 10.3386) plus the NBER feed for the latest week
- CEPR discussion papers, via the paged RSS feed only (CEPR pages are not crawled)
- Articles in 8 journals, via Crossref (by registration date: Crossref often gives only a year
  as publication date): AER, Econometrica, QJE, JPE, REStud, JEL, JEP, Annual Review of Economics

The file is public, so it holds titles, authors and links only, never abstracts.
Each source is fetched on its own. What was collected is always saved; if any source failed,
the script then exits with an error so that the GitHub run shows as failed.
No screening here. Items collected more than 180 days ago are dropped. Standard library only.

  python3 collect_feeds.py                        update routines/flux.json
  python3 collect_feeds.py --abstracts FILE       also write the abstracts the feeds provide to
                                                  FILE (local use only, never commit it)
"""
import datetime as dt
import html
import json
import pathlib
import re
import sys
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
SINCE = (TODAY - dt.timedelta(days=60)).isoformat()
ABSTRACTS = {}  # url -> abstract, kept out of the public file
PAGE = 20  # larger Crossref responses get cut off


def get(url, parse, tries=6):
    """Download and parse; a truncated or unreadable response counts as a failure."""
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return parse(r.read())
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(10)


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(s or ""))).strip()


def crossref(path, kind, source):
    items, offset = [], 0
    while True:
        url = (f"https://api.crossref.org/{path}/works?filter=from-created-date:{SINCE},type:{kind}"
               f"&rows={PAGE}&offset={offset}&sort=created&order=asc"
               "&select=title,author,issued,DOI,abstract,created")
        msg = get(url, json.loads)["message"]
        for w in msg["items"]:
            parts = w.get("issued", {}).get("date-parts", [[None]])[0]
            authors = ", ".join(f"{a.get('given', '')} {a.get('family', '')}".strip()
                                for a in w.get("author", []))
            link = f"https://doi.org/{w['DOI']}"
            items.append({"source": source,
                          "date": "-".join(f"{p:02d}" if i else str(p) for i, p in enumerate(parts) if p),
                          "title": clean((w.get("title") or [""])[0]), "authors": authors, "url": link})
            ABSTRACTS.setdefault(link, clean(w.get("abstract")))
        offset += PAGE
        if offset >= msg["total-results"]:
            break
        if not msg["items"]:
            raise RuntimeError(f"empty page at {offset} of {msg['total-results']}")
    if len(items) < msg["total-results"]:
        raise RuntimeError(f"{len(items)} items for {msg['total-results']} announced")
    return items


def nber():
    items = crossref("prefixes/10.3386", "report", "NBER")
    if not items:
        raise RuntimeError("no item in 60 days")
    return items


def nber_week():
    """Latest week from the NBER feed: Crossref registers these papers a few days later."""
    items = []
    for it in get("https://back.nber.org/rss/new.xml", ET.fromstring).iter("item"):
        title, _, authors = (it.findtext("title") or "").partition(" -- by ")
        link = "https://doi.org/10.3386/" + re.search(r"w\d+", it.findtext("link")).group()
        items.append({"source": "NBER", "date": TODAY.isoformat()[:7], "title": clean(title),
                      "authors": clean(authors), "url": link})
        ABSTRACTS[link] = clean(it.findtext("description"))  # Crossref has none for NBER
    if not items:
        raise RuntimeError("empty feed")
    return items


def cepr():
    ns = {"dc": "http://purl.org/dc/elements/1.1/", "cepr": "https://cepr.org/rss/ns/1.0"}
    items, seen = [], set()
    for page in range(20):
        fresh, oldest = 0, TODAY.isoformat()
        for it in get(f"https://cepr.org/rss/discussion-paper?page={page}", ET.fromstring).iter("item"):
            link = clean(it.findtext("link"))
            date = dt.datetime.strptime((it.findtext("pubDate") or "")[:16], "%a, %d %b %Y").date().isoformat()
            oldest = min(oldest, date)
            if link in seen:
                continue
            seen.add(link)
            fresh += 1
            if date >= SINCE:
                items.append({"source": "CEPR", "date": date, "title": clean(it.findtext("title")),
                              "authors": clean(it.findtext("dc:creator", namespaces=ns)), "url": link,
                              "programme": clean(it.findtext("cepr:programme_areas", namespaces=ns))})
                ABSTRACTS[link] = clean(it.findtext("description"))
        if oldest < SINCE:
            return items
        if not fresh:
            break
        time.sleep(3)
    raise RuntimeError(f"feed does not reach {SINCE}")


def sources():
    yield "NBER (Crossref)", nber
    yield "NBER (feed)", nber_week
    yield "CEPR", cepr
    for name, issn in JOURNALS.items():
        yield name, lambda name=name, issn=issn: crossref(f"journals/{issn}", "journal-article", name)


def main():
    old = json.loads(OUT.read_text()) if OUT.exists() else []
    for i in old:
        i.pop("abstract", None)
    seen = {i["url"] for i in old}
    new, errors = [], []
    for name, fetch in sources():
        try:
            for i in fetch():
                if i["url"] not in seen:
                    i["collecte"] = TODAY.isoformat()
                    new.append(i)
                    seen.add(i["url"])
        except Exception as e:  # one source down must not block the others
            errors.append(f"{name}: {type(e).__name__}: {e}")
    cutoff = (TODAY - dt.timedelta(days=180)).isoformat()
    keep = [i for i in old + new if i["collecte"] >= cutoff]
    keep.sort(key=lambda i: (i["collecte"], i["source"]), reverse=True)
    OUT.write_text(json.dumps(keep, ensure_ascii=False, indent=1) + "\n")
    if "--abstracts" in sys.argv:
        path = pathlib.Path(sys.argv[sys.argv.index("--abstracts") + 1])
        path.write_text(json.dumps(ABSTRACTS, ensure_ascii=False, indent=1))
    print(f"{len(new)} new items, {len(keep)} kept")
    for e in errors:
        print(f"::error::source failed, {e}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
