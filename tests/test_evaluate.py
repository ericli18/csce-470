import datetime

from evaluate import TOPICS, alerts, evaluate, load_json, pool, weeks

D = datetime.date


def test_weeks_cover_range_and_end_is_exclusive():
    assert list(weeks(D(2026, 8, 1), D(2026, 8, 17))) == [
        (D(2026, 8, 1), D(2026, 8, 8)),
        (D(2026, 8, 8), D(2026, 8, 15)),
        (D(2026, 8, 15), D(2026, 8, 17)),
    ]


START, END = D(2026, 8, 1), D(2026, 8, 22)
W1, W2, W3 = weeks(START, END)

# a fake system's ranking of the whole index, and when each paper entered PubMed
RANKING = ["a", "old", "b", "c", "x", "y", "z", "late"]
DATES = {
    "a": D(2026, 8, 2), "b": D(2026, 8, 3), "x": D(2026, 8, 7),  # week 1
    "c": D(2026, 8, 9), "y": D(2026, 8, 14),  # week 2
    "z": D(2026, 8, 15),  # week 3
    "old": D(2026, 7, 31), "late": D(2026, 8, 22),  # outside the window
}


def fake_rank(query):
    return RANKING


def test_alerts_split_ranking_into_weekly_top_k():
    assert alerts(RANKING, DATES, START, END, k=2) == {W1: ["a", "b"], W2: ["c", "y"], W3: ["z"]}


TOPIC = [{"id": "t", "query": "q"}]


def test_precision_skips_weeks_without_relevant_papers():
    qrels = {"t": {"a": 1, "b": 0, "c": 1, "y": 0, "z": 0}}
    r = evaluate(fake_rank, TOPIC, qrels, DATES, START, END, k=2)["t"]
    # week 1: a, b -> 1/2; week 2: c, y -> 1/2; week 3 has no relevant paper, so it is skipped
    assert r["p_at_k"] == 0.5
    assert r["weeks"] == 2
    assert r["unjudged"] == 0.0


def test_unjudged_alerts_count_as_not_relevant():
    qrels = {"t": {"a": 1}}
    r = evaluate(fake_rank, TOPIC, qrels, DATES, START, END, k=2)["t"]
    assert r["p_at_k"] == 0.5  # only week 1 has a known relevant paper
    assert r["unjudged"] == 4 / 5  # b, c, y, z


def test_topic_without_judgments_has_no_score():
    r = evaluate(fake_rank, TOPIC, {}, DATES, START, END, k=2)["t"]
    assert r["p_at_k"] is None


def test_pool_merges_systems_and_skips_judged():
    other = lambda query: ["x", "a"]
    ranks = {"one": fake_rank, "two": other}
    assert pool(ranks, TOPIC[0], {"a": 1}, DATES, START, END, k=2) == ["b", "x", "c", "y", "z"]


def test_topics_file_is_well_formed():
    topics = load_json(TOPICS)
    assert len({t["id"] for t in topics}) == len(topics)
    for t in topics:
        assert t["query"] and t["narrative"] and t["audience"] in ("lay", "researcher")
