"""Build the index, or add any new raw PubMed files to an existing one.

usage (from src/): uv run python -m indexer [--rebuild] [--no-stem]
"""

import argparse
import time

from indexer.index import FIELDS, INDEX_DIR, InvertedIndex
from indexer.normalize import RAW_DIR

parser = argparse.ArgumentParser()
parser.add_argument("--rebuild", action="store_true", help="start from an empty index")
parser.add_argument("--no-stem", action="store_true", help="only applies to a new index")
args = parser.parse_args()

t = time.time()
if (INDEX_DIR / "state.pkl").exists() and not args.rebuild:
    idx = InvertedIndex.load(INDEX_DIR)
    print(f"loaded index: {len(idx):,} docs, {len(idx.files)} files ({time.time() - t:.1f}s)")
else:
    idx = InvertedIndex(stem=not args.no_stem)

t = time.time()
rows = idx.add_files(sorted(RAW_DIR.glob("*.jsonl.gz")))
print(f"added {len(rows):,} docs ({time.time() - t:.1f}s)")
if rows:
    idx.save(INDEX_DIR)

print(f"{len(idx):,} docs, {len(idx.terms):,} terms, stem={idx.stem}")
for f in FIELDS:
    print(f"  {f}: {idx.matrix[f].nnz:,} postings, avg length {idx.avg_len(f):.1f}")
