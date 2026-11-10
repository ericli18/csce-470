"""Inverted index creator"""

import datetime
import pickle
from array import array
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import scipy.sparse as sp

from indexer.normalize import read_raw
from indexer.tokenizer import tokenize
from models import Document

FIELDS = ("title", "abstract")
INDEX_DIR = Path(__file__).resolve().parent.parent / "data" / "index"


class InvertedIndex:
    def __init__(self, stem: bool = True):
        self.stem = stem
        self.terms: list[str] = []  # term id -> term
        self.term_ids: dict[str, int] = {}  # term -> term id
        self.doc_ids: list[str] = []  # row -> PMID
        self.rows: dict[str, int] = {}  # PMID -> row
        self.dates: list[datetime.date] = []  # row -> Entrez date
        self.titles: list[str] = []  # row -> title, for display
        self.files: set[str] = set()  # files that have already been added
        self.matrix = {f: sp.csc_array((0, 0), dtype=np.int32) for f in FIELDS}
        self._update_stats()

    def __len__(self) -> int:
        return len(self.doc_ids)

    # --- building ---

    def add(self, docs: Iterable[Document]) -> range:
        """Index documents not already present (by PMID). Returns their rows."""
        start = len(self)
        # Chose to use CSR format for storing, seems fine https://en.wikipedia.org/wiki/Sparse_matrix#Compressed_sparse_row_(CSR,_CRS_or_Yale_format)
        batch = {f: (array("q", [0]), array("i"), array("i")) for f in FIELDS}
        for doc in docs:
            if doc.doc_id in self.rows:
                continue
            self.rows[doc.doc_id] = len(self)
            self.doc_ids.append(doc.doc_id)
            self.dates.append(doc.date)
            self.titles.append(doc.title)
            for field, (indptr, indices, data) in batch.items():
                counts = Counter(map(self._term_id, tokenize(getattr(doc, field), stem=self.stem)))
                indices.extend(counts.keys())
                data.extend(counts.values())
                indptr.append(len(indices))

        if len(self) == start:
            return range(start, start)
        n_terms = len(self.terms)
        for field, (indptr, indices, data) in batch.items():
            new = sp.csr_array(
                (data, indices, indptr), shape=(len(self) - start, n_terms)
            )
            old = self.matrix[field]
            old.resize((start, n_terms))  # new terms -> empty columns for old docs
            merged = sp.vstack([old, new], format="csc")
            merged.sort_indices()
            self.matrix[field] = merged
        self._update_stats()
        return range(start, len(self))

    def add_files(self, paths: Iterable[Path]) -> range:
        """Index raw PubMed files not added before."""
        new = [p for p in paths if p.name not in self.files]
        rows = self.add(doc for p in new for doc in read_raw(p))
        self.files.update(p.name for p in new)
        return rows

    def _term_id(self, term: str) -> int:
        tid = self.term_ids.get(term)
        if tid is None:
            tid = self.term_ids[term] = len(self.terms)
            self.terms.append(term)
        return tid

    def _update_stats(self):
        self._df = {f: np.diff(m.indptr) for f, m in self.matrix.items()}
        self.doc_len = {
            f: np.asarray(m.sum(axis=1)).ravel() for f, m in self.matrix.items()
        }

    # --- lookups ---

    def postings(self, field: str, term: str) -> tuple[np.ndarray, np.ndarray]:
        """(rows, term frequencies) of the documents containing `term` in `field`."""
        tid = self.term_ids.get(term)
        if tid is None:
            return np.array([], dtype=np.int32), np.array([], dtype=np.int32)
        m = self.matrix[field]
        s, e = m.indptr[tid], m.indptr[tid + 1]
        return m.indices[s:e], m.data[s:e]

    def df(self, field: str, term: str) -> int:
        tid = self.term_ids.get(term)
        return 0 if tid is None else int(self._df[field][tid])

    def avg_len(self, field: str) -> float:
        return float(self.doc_len[field].mean()) if len(self) else 0.0

    # --- persistence ---

    def save(self, path: Path = INDEX_DIR):
        path.mkdir(parents=True, exist_ok=True)
        for field, m in self.matrix.items():
            sp.save_npz(path / f"{field}.npz", m)
        state = {
            "stem": self.stem,
            "terms": self.terms,
            "doc_ids": self.doc_ids,
            "dates": self.dates,
            "titles": self.titles,
            "files": sorted(self.files),
        }
        with open(path / "state.pkl", "wb") as f:
            pickle.dump(state, f)

    @classmethod
    def load(cls, path: Path = INDEX_DIR) -> "InvertedIndex":
        with open(path / "state.pkl", "rb") as f:
            state = pickle.load(f)
        idx = cls(stem=state["stem"])
        idx.terms = state["terms"]
        idx.term_ids = {t: i for i, t in enumerate(idx.terms)}
        idx.doc_ids = state["doc_ids"]
        idx.rows = {d: i for i, d in enumerate(idx.doc_ids)}
        idx.dates = state["dates"]
        idx.titles = state["titles"]
        idx.files = set(state["files"])
        idx.matrix = {f: sp.csc_array(sp.load_npz(path / f"{f}.npz")) for f in FIELDS}
        idx._update_stats()
        return idx
