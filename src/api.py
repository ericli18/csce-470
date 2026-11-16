import datetime
import sqlite3
from contextlib import asynccontextmanager, closing
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response

from indexer.index import InvertedIndex
from models import Alert, AlertCreate, Result, SearchResponse
from rerank import load_features, rerank
from scorer import load_mesh, search

DB_PATH = Path(__file__).resolve().parent / "data" / "alerts.db"

# The data stops at a fixed date, so "new papers" means the last FEED_DAYS
# days of data rather than the days since the alert was created.
FEED_DAYS = 14


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(db()) as conn, conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY,
                query TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )


@dataclass
class Engine:
    """Everything a search needs, loaded once at startup."""

    index: InvertedIndex
    descriptors: list[dict]
    features: dict[str, dict]

    @classmethod
    def load(cls) -> "Engine":
        return cls(InvertedIndex.load(), load_mesh(), load_features())


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.engine = Engine.load()
    app.state.latest = max(app.state.engine.index.dates, default=None)
    yield


app = FastAPI(title="Alertr", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "documents": len(app.state.engine.index)}


@app.get("/search", response_model=SearchResponse)
def search_papers(
    q: str = Query(min_length=1, description="plain-English question"),
    limit: int = Query(20, ge=1, le=100),
    since: datetime.date | None = Query(None, description="only papers added on or after this date"),
    until: datetime.date | None = Query(None, description="only papers added on or before this date"),
    mesh: bool = Query(True, description="expand the query with MeSH synonyms"),
    use_rerank: bool = Query(True, alias="rerank", description="boost stronger study types"),
):
    eng: Engine = app.state.engine
    idx = eng.index

    results = search(idx, q, eng.descriptors if mesh else None)
    if use_rerank:
        results = rerank(results, eng.features)
        # retracted papers get a prior of 0; don't show them at all
        results = [(pmid, score) for pmid, score in results if score > 0]

    matches = []
    for pmid, score in results:
        date = idx.dates[idx.rows[pmid]]
        if since is not None and date < since:
            continue
        if until is not None and date > until:
            continue
        matches.append((pmid, score, date))

    out = []
    for pmid, score, date in matches[:limit]:
        f = eng.features.get(pmid, {})
        out.append(
            Result(
                pmid=pmid,
                title=idx.titles[idx.rows[pmid]],
                date=date,
                score=round(score, 4),
                pub_types=f.get("pub_types", []),
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            )
        )
    return SearchResponse(query=q, total=len(matches), results=out)


# --- alerts ---


def get_alert(alert_id: int) -> Alert:
    with closing(db()) as conn:
        row = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "alert not found")
    return Alert(**row)


@app.post("/alerts", response_model=Alert, status_code=201)
def create_alert(body: AlertCreate):
    created_at = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
    with closing(db()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO alerts (query, created_at) VALUES (?, ?)", (body.query, created_at)
        )
    return get_alert(cur.lastrowid)


@app.get("/alerts", response_model=list[Alert])
def list_alerts():
    with closing(db()) as conn:
        rows = conn.execute("SELECT * FROM alerts ORDER BY id DESC").fetchall()
    return [Alert(**r) for r in rows]


@app.delete("/alerts/{alert_id}", status_code=204)
def delete_alert(alert_id: int):
    with closing(db()) as conn, conn:
        cur = conn.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
    if cur.rowcount == 0:
        raise HTTPException(404, "alert not found")
    return Response(status_code=204)


@app.get("/alerts/{alert_id}/feed", response_model=SearchResponse)
def alert_feed(
    alert_id: int,
    limit: int = Query(20, ge=1, le=100),
    since: datetime.date | None = Query(
        None, description=f"defaults to the last {FEED_DAYS} days of data"
    ),
):
    alert = get_alert(alert_id)
    if since is None and app.state.latest is not None:
        since = app.state.latest - datetime.timedelta(days=FEED_DAYS)
    return search_papers(
        q=alert.query, limit=limit, since=since, until=None, mesh=True, use_rerank=True
    )
