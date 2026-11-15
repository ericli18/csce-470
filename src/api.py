import datetime
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, Query

from indexer.index import InvertedIndex
from models import Result, SearchResponse
from rerank import load_features, rerank
from scorer import load_mesh, search


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
    app.state.engine = Engine.load()
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
