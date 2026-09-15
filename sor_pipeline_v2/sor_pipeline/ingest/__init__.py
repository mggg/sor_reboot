"""Stage 1 — ingest: fetch raw data from sources and store it locally.

Reads from the Census API, TIGER/Line, and the election CSVs, and writes the
untouched pulls into data/raw/. Nothing here derives or cleans; it only acquires
and persists, so the expensive network fetches happen once.
"""
