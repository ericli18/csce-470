# Alertr

Our project sends people alerts about new research on a question they care about.
You type something in plain English like "effects of creatine on human bodies", and
it finds and ranks new PubMed papers that match. This is our Stage 1 version: the
core search and ranking, plus tests and an evaluation setup.

## How it works

1. **Collect** papers from PubMed by the date they were added, plus the MeSH
   vocabulary (NLM's list of medical terms and their synonyms).
2. **Normalize and tokenize** titles and abstracts: lowercase, strip HTML, remove
   stopwords, stem.
3. **Index** everything into an inverted index (sparse matrix per field). New days
   can be added without rebuilding.
4. **Score** with BM25 over title and abstract (title counts double). Before
   searching, we expand the query with MeSH synonyms, so "heart attack" also
   matches "myocardial infarction". Expanded terms get half the weight of the
   user's own words.
5. **Rerank** by study type. Meta-analyses, reviews and trials move up; animal-only
   studies, editorials and retracted papers move down. Most of our users aren't
   experts, so we want the stronger evidence first.
6. **Evaluate** by replaying past weeks as if they were alerts and measuring P@5
   against papers we labeled by hand.

## Setup

You need Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```sh
# install uv (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# install dependencies
uv sync
```

Dependencies (installed by `uv sync`): numpy, scipy, pydantic, pystemmer,
requests, pandas, matplotlib, and pytest for tests.

## Run the tests

No data download needed. The tests build a tiny index from a few made-up papers.

```sh
uv run pytest
```

What they check:
- `test_scorer.py`: BM25 finds the right paper, and MeSH expansion lets
  "heart attack" find a paper titled "Myocardial infarction treatment"
- `test_rerank.py`: a meta-analysis outranks a case report, animal-only studies
  get penalized, retracted papers drop to zero
- `test_tokenizer.py`, `test_normalize.py`, `test_index.py`: text cleaning and
  indexing
- `test_evaluate.py`: the weekly alert and P@k logic

## Running on real data

The data isn't in the repo (it's a few hundred MB). To download it yourself:

```sh
cd src
uv run scripts/collect_mesh.py                          # a few minutes
uv run scripts/collect_pubmed.py 2026-08-01 2026-10-25  # 1-3 hours, safe to stop and resume
cd ..
```

Then build the index and run the evaluation:

```sh
uv run --directory src python -m indexer             # add --rebuild to start over
uv run --directory src python evaluate.py judge --start 2026-08-01 --end 2026-10-25 --topics t01,t02
uv run --directory src python evaluate.py run --start 2026-08-01 --end 2026-10-25
```

`judge` shows you papers one at a time to label as relevant or not (saved to
`src/qrels.json`). `run` prints P@5 for plain BM25 vs. BM25 + MeSH for each topic.
The 17 test topics are in `src/topics.json`.
