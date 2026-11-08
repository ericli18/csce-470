"""Harvest arXiv metadata via OAI-PMH (metadataPrefix=arXiv) for a datestamp window.

usage: uv run scripts/collect_arxiv.py 2026-08-01 2026-10-25
"""

import gzip
import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

BASE = "https://oaipmh.arxiv.org/oai"
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "arxiv"
NS = {"oai": "http://www.openarchives.org/OAI/2.0/", "a": "http://arxiv.org/OAI/arXiv/"}


def text(el, path):
    node = el.find(path, NS)
    return " ".join(node.text.split()) if node is not None and node.text else None


def parse_record(rec):
    header = rec.find("oai:header", NS)
    if header.get("status") == "deleted":
        return None
    meta = rec.find("oai:metadata/a:arXiv", NS)
    authors = meta.findall("a:authors/a:author", NS)
    return {
        "id": text(meta, "a:id"),
        "datestamp": text(header, "oai:datestamp"),
        "created": text(meta, "a:created"),
        "updated": text(meta, "a:updated"),
        "title": text(meta, "a:title"),
        "abstract": text(meta, "a:abstract"),
        "categories": (text(meta, "a:categories") or "").split(),
        "n_authors": len(authors),
        "comments": text(meta, "a:comments"),
        "journal_ref": text(meta, "a:journal-ref"),
        "doi": text(meta, "a:doi"),
    }


def fetch(params):
    for attempt in range(8):
        r = requests.get(BASE, params=params, timeout=120)
        if r.status_code == 503:
            wait = int(r.headers.get("Retry-After", 30))
            print(f"  503, retry after {wait}s", flush=True)
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.content
    raise RuntimeError("too many retries")


def main(start, end):
    OUT.mkdir(parents=True, exist_ok=True)
    state = OUT / "_resume.json"
    if state.exists():
        page, token = json.loads(state.read_text()).values()
        params = {"verb": "ListRecords", "resumptionToken": token}
    else:
        page = 0
        params = {"verb": "ListRecords", "metadataPrefix": "arXiv", "from": start, "until": end}

    while True:
        root = ET.fromstring(fetch(params))
        records = [r for r in map(parse_record, root.iterfind(".//oai:record", NS)) if r]
        with gzip.open(OUT / f"page_{page:04d}.jsonl.gz", "wt") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")
        tok = root.find(".//oai:resumptionToken", NS)
        total = tok.get("completeListSize") if tok is not None else "?"
        print(f"page {page}: {len(records)} records (list size {total})", flush=True)
        if tok is None or not (tok.text or "").strip():
            break
        page += 1
        params = {"verb": "ListRecords", "resumptionToken": tok.text.strip()}
        state.write_text(json.dumps({"page": page, "token": tok.text.strip()}))
        time.sleep(1)

    state.unlink(missing_ok=True)
    print("done")


if __name__ == "__main__":
    main(*sys.argv[1:3])
