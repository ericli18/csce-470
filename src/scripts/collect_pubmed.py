"""Harvest PubMed records by Entrez date (the date a record enters PubMed, i.e.
when an alert would fire) using NCBI E-utilities.

usage: uv run scripts/collect_pubmed.py 2026-08-01 2026-10-25
"""

import datetime as dt
import gzip
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "pubmed"
BATCH = 400
COMMON = {"db": "pubmed", "tool": "csce470-paper-alerts"}
if os.environ.get("NCBI_API_KEY"):
    COMMON["api_key"] = os.environ["NCBI_API_KEY"]
DELAY = 0.12 if "api_key" in COMMON else 0.4


def request(endpoint, data):
    for attempt in range(6):
        try:
            r = requests.post(f"{EUTILS}/{endpoint}", data={**COMMON, **data}, timeout=180)
            if r.status_code in (429, 500, 502, 503):
                raise requests.HTTPError(str(r.status_code))
            r.raise_for_status()
            time.sleep(DELAY)
            return r
        except (requests.RequestException, ET.ParseError) as e:
            print(f"  {endpoint} failed ({e}), retrying", flush=True)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{endpoint} failed repeatedly")


def all_text(el):
    return " ".join("".join(el.itertext()).split()) if el is not None else None


def date_of(el):
    if el is None:
        return None
    y, m, d = (el.findtext(k) for k in ("Year", "Month", "Day"))
    return f"{y}-{int(m):02d}-{int(d):02d}" if y and m and m.isdigit() and d else y


def parse_article(art):
    mc = art.find("MedlineCitation")
    a = mc.find("Article")
    abstract_parts = a.findall("Abstract/AbstractText")
    history = {d.get("PubStatus"): date_of(d) for d in art.findall("PubmedData/History/PubMedPubDate")}
    ids = {i.get("IdType"): i.text for i in art.findall("PubmedData/ArticleIdList/ArticleId")}
    return {
        "pmid": mc.findtext("PMID"),
        "status": mc.get("Status"),
        "indexing_method": mc.get("IndexingMethod"),
        "entrez_date": history.get("entrez"),
        "pubmed_date": history.get("pubmed"),
        "title": all_text(a.find("ArticleTitle")),
        "abstract": " ".join(all_text(p) for p in abstract_parts) or None,
        "abstract_structured": any(p.get("Label") for p in abstract_parts),
        "journal": a.findtext("Journal/Title"),
        "journal_abbrev": a.findtext("Journal/ISOAbbreviation"),
        "language": [l.text for l in a.findall("Language")],
        "pub_types": [p.text for p in a.findall("PublicationTypeList/PublicationType")],
        "mesh": [
            {"ui": d.get("UI"), "name": d.text, "major": d.get("MajorTopicYN") == "Y"}
            for d in mc.findall("MeshHeadingList/MeshHeading/DescriptorName")
        ],
        "keywords": [all_text(k) for k in mc.findall("KeywordList/Keyword")],
        "n_authors": len(a.findall("AuthorList/Author")),
        "doi": ids.get("doi"),
        "pmc": ids.get("pmc"),
    }


def search(term):
    """esearch returns at most 9,999 ids, so split busy days by MEDLINE subset."""
    r = request("esearch.fcgi", {"term": term, "retmax": 9999, "retmode": "json"})
    res = r.json()["esearchresult"]
    if int(res["count"]) <= len(res["idlist"]):
        return res["idlist"]
    if "medline[sb]" in term:
        print(f"  WARNING {term}: {res['count']} hits, only {len(res['idlist'])} retrievable", flush=True)
        return res["idlist"]
    return search(f"{term} AND medline[sb]") + search(f"{term} NOT medline[sb]")


def harvest_day(day):
    out = OUT / f"{day}.jsonl.gz"
    if out.exists():
        return
    d = day.replace("-", "/")
    pmids = search(f'"{d}"[edat]')

    tmp = out.with_suffix(".tmp")
    n = 0
    with gzip.open(tmp, "wt") as f:
        for i in range(0, len(pmids), BATCH):
            r = request("efetch.fcgi", {"id": ",".join(pmids[i : i + BATCH]), "retmode": "xml"})
            for art in ET.fromstring(r.content).iterfind("PubmedArticle"):
                f.write(json.dumps(parse_article(art)) + "\n")
                n += 1
    tmp.rename(out)
    print(f"{day}: {n} records", flush=True)


def main(start, end):
    OUT.mkdir(parents=True, exist_ok=True)
    day, last = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    while day <= last:
        harvest_day(day.isoformat())
        day += dt.timedelta(days=1)
    print("done")


if __name__ == "__main__":
    main(*sys.argv[1:3])
