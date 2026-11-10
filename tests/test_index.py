import datetime

import pytest

from indexer.index import InvertedIndex
from models import Document


def doc(doc_id, title, abstract=""):
    return Document(doc_id=doc_id, title=title, abstract=abstract, date=datetime.date(2026, 8, 1), mesh=[], meta={})


# two batches, like two days of new papers arriving
DAY_1 = [
    doc("1", "Heart attack in women", "Heart attack symptoms differ in women. Women report fatigue."),
    doc("2", "Vancomycin-resistant enterococci", "Resistant enterococci were isolated."),
]
DAY_2 = [
    doc("3", "COVID-19 and heart failure"),  # new terms after the first batch
    doc("1", "Duplicate record should be skipped"),  # PMID already indexed
]


@pytest.fixture(scope="module", params=["in-memory", "saved-and-loaded"])
def index(request, tmp_path_factory):
    idx = InvertedIndex()
    idx.add(DAY_1)
    idx.add(DAY_2)
    if request.param == "saved-and-loaded":
        path = tmp_path_factory.mktemp("index")
        idx.save(path)
        idx = InvertedIndex.load(path)
    return idx


# (field, stemmed term, expected {PMID: term frequency})
CASES = [
    ("title", "heart", {"1": 1, "3": 1}),
    ("abstract", "heart", {"1": 1}),
    ("title", "women", {"1": 1}),
    ("abstract", "women", {"1": 2}),
    ("abstract", "symptom", {"1": 1}),
    ("abstract", "fatigu", {"1": 1}),
    ("title", "resist", {"2": 1}),
    ("abstract", "resist", {"2": 1}),
    ("title", "enterococci", {"2": 1}),
    ("abstract", "isol", {"2": 1}),
    # terms first seen in the second batch
    ("title", "covid", {"3": 1}),
    ("title", "19", {"3": 1}),
    ("title", "failur", {"3": 1}),
    ("abstract", "covid", {}),
    # duplicate PMID was skipped, unknown term is empty
    ("title", "duplic", {}),
    ("title", "cancer", {}),
]


@pytest.mark.parametrize("field, term, expected", CASES)
def test_postings(index, field, term, expected):
    rows, tfs = index.postings(field, term)
    assert {index.doc_ids[r]: int(tf) for r, tf in zip(rows, tfs)} == expected
