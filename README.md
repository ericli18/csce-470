# Alertr

Finds and ranks new PubMed papers that match a plain-English question.

## Setup

You need Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh   # install uv (macOS/Linux)
uv sync                                           # install dependencies
```

## Run the tests

No data download needed.

```sh
uv run pytest
```

## Get the data

The data isn't in the repo (it's a few hundred MB).

```sh
cd src
uv run scripts/collect_mesh.py                          # a few minutes
uv run scripts/collect_pubmed.py 2026-08-01 2026-10-25  # 1-3 hours, safe to stop and resume
cd ..
uv run --directory src python -m indexer                # build the index; add --rebuild to start over
```

## Run the search API

```sh
uv run --directory src uvicorn api:app --reload
```

Startup takes about 10 seconds. API docs are at http://127.0.0.1:8000/docs.

```sh
curl 'http://127.0.0.1:8000/search?q=effects+of+creatine+on+human+bodies&limit=5'
```

## Run the evaluation

```sh
uv run --directory src python evaluate.py judge --start 2026-08-01 --end 2026-10-25 --topics t01,t02  # label papers by hand
uv run --directory src python evaluate.py run --start 2026-08-01 --end 2026-10-25                     # print P@5 per topic
```
