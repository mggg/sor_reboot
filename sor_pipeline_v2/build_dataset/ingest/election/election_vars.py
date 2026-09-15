"""What the election source declares: the political-preference features. Group K.

The derived fields are computed in the clean stage from the raw two-party vote
columns this source loads:

  VOTELEAN       = (Rep - Dem) / total two-party vote; positive = Republican
  NUMBEROFVOTERS = Dem + Rep (total two-party vote)
  TURNOUT        = NUMBEROFVOTERS / VOTINGAGEPOP (two-party votes cast per
                   voting-age resident; denominators meet only after the ACS join)
"""

from __future__ import annotations

# (feature name, meaning). TURNOUT and NUMBEROFVOTERS sit under the elections
# group though they measure participation and size; only VOTELEAN is
# preference proper -- see the manifest's judgment-call notes.
ELECTION_FEATURES: tuple[tuple[str, str], ...] = (
    ("VOTELEAN",
     "(Republican - Democratic) share of the two-party 2020 presidential "
     "vote; positive = Republican-leaning"),
    ("NUMBEROFVOTERS",
     "Total two-party 2020 presidential vote (Dem + Rep)"),
    ("TURNOUT",
     "Two-party 2020 presidential votes cast per voting-age resident"),
)
