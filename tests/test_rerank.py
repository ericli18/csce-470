from rerank import prior, rerank


def make(pub_types=None, mesh=None, title_words=None):
    return {
        "pub_types": pub_types or [],
        "mesh": set(mesh or []),
        "title_words": set(title_words or []),
    }


def test_meta_analysis_beats_case_report():
    features = {
        "1": make(pub_types=["Case Reports"]),
        "2": make(pub_types=["Meta-Analysis"]),
    }
    results = rerank([("1", 10.0), ("2", 10.0)], features)
    assert results[0][0] == "2"


def test_animal_only_penalized():
    assert prior(make(mesh=["Animals", "Mice"])) < 1.0
    assert prior(make(mesh=["Animals", "Humans"])) == 1.0


def test_animal_words_when_no_mesh():
    assert prior(make(title_words=["creatine", "mice"])) < 1.0


def test_retracted_is_zero():
    assert prior(make(pub_types=["Meta-Analysis", "Retracted Publication"])) == 0.0
