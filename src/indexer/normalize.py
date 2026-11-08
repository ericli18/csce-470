"""Normalize raw PubMed records into Documents."""

import gzip
import html
import json
import re
from collections.abc import Iterator
from pathlib import Path

from models import Document, MeshHeading

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "pubmed"

# raw fields mapped onto Document; everything else goes to meta
CONSUMED = {"pmid", "title", "abstract", "entrez_date", "mesh"}

# regex parsing to match my test cases
INLINE_TAG = re.compile(r"</?(?:em|i|b|u|sup|sub)>", re.IGNORECASE)


def clean_text(s: str | None) -> str:
    if not s:
        return ""
    s = html.unescape(s)
    s = INLINE_TAG.sub("", s)
    return " ".join(s.split())


def clean_title(s: str | None) -> str:
    s = clean_text(s).removesuffix(".")
    # PubMed wraps English translations of non-English titles in brackets
    # (a few are double-wrapped: "[[Title]]")
    while s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip()
    return s


def normalize(rec: dict) -> Document | None:
    title = clean_title(rec.get("title"))
    if not title:
        return None
    return Document(
        doc_id=rec["pmid"],
        title=title,
        abstract=clean_text(rec.get("abstract")),
        date=rec["entrez_date"],
        mesh=[
            MeshHeading(descriptor_id=m["ui"], name=m["name"], major_topic=m["major"])
            for m in rec.get("mesh") or []
        ],
        meta={k: v for k, v in rec.items() if k not in CONSUMED},
    )


def read_raw(path: Path) -> Iterator[Document]:
    with gzip.open(path, "rt") as f:
        for line in f:
            doc = normalize(json.loads(line))
            if doc is not None:
                yield doc


def iter_documents(root: Path = RAW_DIR) -> Iterator[Document]:
    for path in sorted(root.glob("*.jsonl.gz")):
        yield from read_raw(path)
