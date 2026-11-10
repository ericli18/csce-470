# csce-470

The `src/scripts` holds the data collection, but you can ask Eric for the data otherwise

```sh
# Build/append to inverted index
uv run --directory src python -m indexer
# Rebuild inverted index
uv run --directory src python -m indexer -- rebuild
```
