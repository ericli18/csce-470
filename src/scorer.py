import gzip
import json
import math
from pathlib import Path

from indexer.tokenizer import tokenize


MESH_PATH = Path(__file__).resolve().parent / "data" / "mesh" / "mesh_descriptors.jsonl.gz"


def load_mesh(path=MESH_PATH):
    """Load the MeSH descriptors collected by collect_mesh.py."""
    descriptors = []
    with gzip.open(path, "rt", encoding="utf-8") as file:
        for line in file:
            descriptor = json.loads(line)
            descriptors.append(descriptor)
    return descriptors


def contains_phrase(query_tokens, phrase_tokens):
    """Check whether a phrase occurs in the tokenized query."""
    phrase_length = len(phrase_tokens)
    if phrase_length == 0:
        return False
    last_start = len(query_tokens) - phrase_length

    for start in range(last_start + 1):
        matched = True
        for offset in range(phrase_length):
            if query_tokens[start + offset] != phrase_tokens[offset]:
                matched = False
                break
        if matched:
            return True

    return False


def expand_query(query, descriptors, stem=True):
    """Create a weighted query using matching MeSH descriptors."""
    query_tokens = tokenize(query, stem=stem)
    term_weights = {}

    # original query terms have full weight so 1
    for term in query_tokens:
        term_weights[term] = 1.0

    for descriptor in descriptors:
        phrases = [descriptor["name"]]
        for entry_term in descriptor["entry_terms"]:
            phrases.append(entry_term)

        #check if query contains the descriptor name or term
        descriptor_matches = False
        for phrase in phrases:
            phrase_tokens = tokenize(phrase, stem=stem)
            if contains_phrase(query_tokens, phrase_tokens):
                descriptor_matches = True
                break

        if descriptor_matches:
            # added terms less weight than the original query terms
            for phrase in phrases:
                phrase_tokens = tokenize(phrase, stem=stem)
                for term in phrase_tokens:
                    if term not in term_weights:
                        term_weights[term] = 0.5

    return term_weights


def search(index, query, descriptors=None, k1=1.2, b=0.75):
    """Return matching (PMID, score) pairs, highest score first."""
    if len(index) == 0:
        return []
    if descriptors is None:
        descriptors = []

    term_weights = expand_query(query, descriptors, stem=index.stem)

    #scores are stored by index row numbr
    scores = {}

    fields = ["title", "abstract"]
    field_weights = {
        "title": 2.0,
        "abstract": 1.0,
    }

    document_count = len(index)
    for field in fields:
        average_length = index.avg_len(field)

        #ignore if empty
        if average_length == 0:
            continue

        for term in term_weights:
            query_weight = term_weights[term]
            rows, frequencies = index.postings(field, term)
            if len(rows) == 0:
                continue
            document_frequency = index.df(field, term)

            # IDF
            numerator = document_count - document_frequency + 0.5
            denominator = document_frequency + 0.5
            idf = math.log(1 + numerator / denominator)

            for position in range(len(rows)):
                row = int(rows[position])
                term_frequency = int(frequencies[position])
                document_length = index.doc_len[field][row]

                length_factor = 1 - b + b * document_length / average_length

                numerator = term_frequency * (k1 + 1)
                denominator = term_frequency + k1 * length_factor

                bm25_score = idf * numerator / denominator
                weighted_score = bm25_score * query_weight * field_weights[field]

                if row not in scores:
                    scores[row] = 0.0

                scores[row] = scores[row] + weighted_score

    #PMIDS
    results = []
    for row in scores:
        pmid = index.doc_ids[row]
        score = scores[row]
        results.append((pmid, score))

    #high to low
    results.sort(key=get_score, reverse=True)

    return results

def get_score(result):
    return result[1]