"""Stage 2 — clean: merge the raw sources and derive analysis-ready columns.

Takes the raw pulls from data/raw/, merges them on GEOID, renames raw census
codes to readable names, computes VOTELEAN / DENSITY / derived race counts and
shares, drops invalid rows, and writes the result to data/processed/.
"""
