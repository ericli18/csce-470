from indexer.normalize import iter_documents
from indexer.tokenizer import tokenize

# Multiplier for each publication type. Above 1 means stronger evidence,
# below 1 means weaker. Types not listed here stay at 1.0.
STUDY_WEIGHTS = {
    "Meta-Analysis": 1.5,
    "Systematic Review": 1.5,
    "Randomized Controlled Trial": 1.3,
    "Clinical Trial": 1.15,
    "Review": 1.1,
    "Case Reports": 0.8,
    "Editorial": 0.6,
    "Comment": 0.6,
    "Letter": 0.6,
}

ANIMAL_PENALTY = 0.7

# Used when a paper has no MeSH tags yet (new papers usually don't)
ANIMAL_WORDS = {"mice", "mouse", "rat", "rats", "murine", "zebrafish", "rodent", "rodents"}


def load_features():
    features = {}
    for doc in iter_documents():
        mesh_names = set()
        for heading in doc.mesh:
            mesh_names.add(heading.name)

        features[doc.doc_id] = {
            "pub_types": doc.meta.get("pub_types") or [],
            "mesh": mesh_names,
            "title_words": set(tokenize(doc.title, stem=False)),
        }
    return features


def is_animal_only(f):
    if len(f["mesh"]) > 0:
        return "Animals" in f["mesh"] and "Humans" not in f["mesh"]
    return len(f["title_words"] & ANIMAL_WORDS) > 0


def prior(f):
    if "Retracted Publication" in f["pub_types"]:
        return 0.0

    matched = []
    for pub_type in f["pub_types"]:
        if pub_type in STUDY_WEIGHTS:
            matched.append(STUDY_WEIGHTS[pub_type])

    weight = 1.0
    if len(matched) > 0:
        weight = max(matched)

    if is_animal_only(f):
        weight = weight * ANIMAL_PENALTY

    return weight


def rerank(results, features):
    rescored = []
    for pmid, score in results:
        f = features.get(pmid)
        if f is not None:
            score = score * prior(f)
        rescored.append((pmid, score))

    rescored.sort(key=lambda r: r[1], reverse=True)
    return rescored
