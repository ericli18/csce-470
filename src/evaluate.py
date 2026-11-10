import argparse
import datetime
import json
import textwrap
from collections.abc import Callable, Iterator
from pathlib import Path

from indexer.index import InvertedIndex
from indexer.normalize import iter_documents
from scorer import load_mesh, search

HERE = Path(__file__).resolve().parent
TOPICS = HERE / "topics.json"
QRELS = HERE / "qrels.json"

Rank = Callable[[str], list[str]]
Window = tuple[datetime.date, datetime.date]
Qrels = dict[str, dict[str, int]] 


def weeks(start: datetime.date, end: datetime.date) -> Iterator[Window]:
    week = datetime.timedelta(days=7)
    while start < end:
        yield start, min(start + week, end)
        start += week


def systems(idx: InvertedIndex) -> dict[str, Rank]:
    descriptors = load_mesh()
    return {
        "bm25": lambda query: [pmid for pmid, _ in search(idx, query)],
        "bm25+mesh": lambda query: [pmid for pmid, _ in search(idx, query, descriptors)],
    }


def alerts(ranking: list[str], dates: dict[str, datetime.date], start, end, k) -> dict[Window, list[str]]:
    windows = list(weeks(start, end))
    out: dict[Window, list[str]] = {w: [] for w in windows}
    for pmid in ranking:
        d = dates[pmid]
        if start <= d < end:
            top = out[windows[(d - start).days // 7]]
            if len(top) < k:
                top.append(pmid)
    return out


def evaluate(
    rank: Rank,
    topics: list[dict],
    qrels: Qrels,
    dates: dict[str, datetime.date],
    start: datetime.date,
    end: datetime.date,
    k: int,
) -> dict[str, dict]:

    results = {}
    for t in topics:
        judged = qrels.get(t["id"], {})
        relevant_dates = [dates[p] for p, rel in judged.items() if rel and p in dates]
        precisions, shown, unjudged = [], 0, 0
        for (ws, we), top in alerts(rank(t["query"]), dates, start, end, k).items():
            shown += len(top)
            unjudged += sum(p not in judged for p in top)
            if any(ws <= d < we for d in relevant_dates):
                precisions.append(sum(judged.get(p, 0) for p in top) / k)
        results[t["id"]] = {
            "p_at_k": sum(precisions) / len(precisions) if precisions else None,
            "weeks": len(precisions),
            "unjudged": unjudged / shown if shown else 0.0,
        }
    return results


def pool(ranks: dict[str, Rank], topic: dict, judged: dict[str, int], dates, start, end, k) -> list[str]:
    weekly = [alerts(rank(topic["query"]), dates, start, end, k) for rank in ranks.values()]
    seen: dict[str, None] = {}
    for w in weeks(start, end):
        for system_alerts in weekly:
            for p in system_alerts[w]:
                if p not in judged:
                    seen.setdefault(p)
    return list(seen)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_qrels(qrels: Qrels):
    QRELS.write_text(json.dumps(qrels, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def judge(ranks: dict[str, Rank], topics: list[dict], qrels: Qrels, dates, start, end, k):
    pools = {t["id"]: pool(ranks, t, qrels.get(t["id"], {}), dates, start, end, k) for t in topics}
    needed = set().union(*pools.values())
    print(f"{len(needed)} papers to judge; reading abstracts...")
    docs = {d.doc_id: d for d in iter_documents() if d.doc_id in needed}

    for t in topics:
        todo = pools[t["id"]]
        for i, pmid in enumerate(todo, 1):
            doc = docs.get(pmid)
            print(f"\n[{t['id']} {i}/{len(todo)}] {t['query']}")
            print(textwrap.fill(t["narrative"], 100, initial_indent="  ", subsequent_indent="  "))
            print(f"\nhttps://pubmed.ncbi.nlm.nih.gov/{pmid}/")
            if doc:
                print(doc.title)
                print(textwrap.fill(doc.abstract[:1500] or "(no abstract)", 100))
            answer = ""
            while answer not in ("y", "n", "s", "q"):
                answer = input("relevant? [y]es [n]o [s]kip [q]uit: ").strip().lower()
            if answer == "q":
                return
            if answer != "s":
                qrels.setdefault(t["id"], {})[pmid] = int(answer == "y")
                save_qrels(qrels)


def report(ranks: dict[str, Rank], topics: list[dict], qrels: Qrels, dates, start, end, k):
    results = {name: evaluate(rank, topics, qrels, dates, start, end, k) for name, rank in ranks.items()}

    names = list(results)
    print(f"{'topic':6} {'audience':10} " + " ".join(f"{n:>12}" for n in names) + "  weeks  query")
    for t in topics:
        row = [results[n][t["id"]]["p_at_k"] for n in names]
        cells = " ".join(f"{'-' if p is None else f'{p:.3f}':>12}" for p in row)
        weeks_used = results[names[0]][t["id"]]["weeks"]
        print(f"{t['id']:6} {t['audience']:10} {cells}  {weeks_used:5}  {t['query']}")

    print()
    for n in names:
        scored = [r for r in results[n].values() if r["p_at_k"] is not None]
        mean = sum(r["p_at_k"] for r in scored) / len(scored) if scored else 0.0
        unjudged = sum(r["unjudged"] for r in results[n].values()) / len(topics)
        print(f"{n:>12}: mean P@{k} = {mean:.3f} over {len(scored)} topics, {unjudged:.0%} of alerts unjudged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["judge", "run"])
    parser.add_argument("--start", type=datetime.date.fromisoformat, required=True)
    parser.add_argument("--end", type=datetime.date.fromisoformat, required=True)
    parser.add_argument("-k", type=int, default=5)
    parser.add_argument("--topics", help="comma-separated topic ids (default: all)")
    args = parser.parse_args()

    topics = load_json(TOPICS)
    if args.topics:
        wanted = set(args.topics.split(","))
        topics = [t for t in topics if t["id"] in wanted]
    qrels = load_json(QRELS)
    idx = InvertedIndex.load()
    dates = dict(zip(idx.doc_ids, idx.dates))
    ranks = systems(idx)

    if args.command == "judge":
        judge(ranks, topics, qrels, dates, args.start, args.end, args.k)
    else:
        report(ranks, topics, qrels, dates, args.start, args.end, args.k)
