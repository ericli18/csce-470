import datetime

from indexer.index import InvertedIndex
from models import Document
from scorer import expand_query, search


def create_document(pmid, title):
    return Document(
        doc_id=pmid,
        title=title,
        abstract="",
        date=datetime.date(2026, 8, 1),
        mesh=[],
        meta={},
    )


def create_index():
    index = InvertedIndex()

    documents = [
        create_document("1", "Heart attack recovery"),
        create_document("2", "Myocardial infarction treatment"),
        create_document("3", "Diabetes treatment"),
    ]

    index.add(documents)
    return index


def create_mesh():
    descriptor = {
        "ui": "D009203",
        "name": "Myocardial Infarction",
        "trees": [],
        "entry_terms": ["Heart Attack"],
    }

    return [descriptor]


def test_bm25_finds_matching_document():
    index = create_index()
    results = search(index, "diabetes")

    assert len(results) == 1
    assert results[0][0] == "3"
    assert results[0][1] > 0


def test_mesh_expansion_finds_related_document():
    index = create_index()
    mesh = create_mesh()

    results_without_mesh = search(index, "heart attack")
    results_with_mesh = search(index, "heart attack", mesh)

    assert len(results_without_mesh) == 1
    assert results_without_mesh[0][0] == "1"

    assert len(results_with_mesh) == 2
    assert results_with_mesh[0][0] == "1"
    assert results_with_mesh[1][0] == "2"


def test_original_terms_have_more_weight():
    mesh = create_mesh()
    terms = expand_query("heart attack", mesh)

    assert terms["heart"] == 1.0
    assert terms["myocardi"] == 0.5


def test_unknown_query():
    index = create_index()
    results = search(index, "unrelated")

    assert results == []


def test_empty_index():
    index = InvertedIndex()
    results = search(index, "heart attack")

    assert results == []