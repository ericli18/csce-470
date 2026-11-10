"""
usage: uv run scripts/collect_mesh.py [year]
"""

import gzip
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parent.parent / "data" / "mesh"


def main(year="2026"):
    OUT.mkdir(parents=True, exist_ok=True)
    src = OUT / f"desc{year}.gz"

    if not src.exists():
        url = f"https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc{year}.gz"
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        src.write_bytes(response.content)

    # Check whether the downloaded file is actually gzip-compressed.
    with open(src, "rb") as source:
        first_two_bytes = source.read(2)

    if first_two_bytes == b"\x1f\x8b":
        open_source = gzip.open
    else:
        open_source = open

    n = 0
    with open_source(src, "rb") as file:
        with gzip.open(OUT / "mesh_descriptors.jsonl.gz", "wt") as out:
            for _, el in ET.iterparse(file):
                if el.tag != "DescriptorRecord":
                    continue
                name = el.findtext("DescriptorName/String")
                terms = {t.text for t in el.iterfind("ConceptList/Concept/TermList/Term/String")}
                out.write(json.dumps({
                    "ui": el.findtext("DescriptorUI"),
                    "name": name,
                    "trees": [t.text for t in el.iterfind("TreeNumberList/TreeNumber")],
                    "entry_terms": sorted(terms - {name}),
                }) + "\n")
                n += 1
                el.clear()
    print(f"{n} descriptors")


if __name__ == "__main__":
    main(*sys.argv[1:2])
