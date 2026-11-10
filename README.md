# csce-470

The `src/scripts` holds the data collection, but you can ask Eric for the data otherwise

```sh
# Build/append to inverted index
uv run --directory src python -m indexer
# Rebuild inverted index
uv run --directory src python -m indexer --rebuild
# Evaluate: label pooled alerts into src/qrels.json, then score each system week by week
uv run --directory src python evaluate.py judge --start 2026-08-01 --end 2026-10-25 --topics t01,t02
uv run --directory src python evaluate.py run --start 2026-08-01 --end 2026-10-25
```
