"""The column glossary written beside every report.

Several of these column names were opaque enough to need explaining out
loud, so the explanation now ships with the numbers instead of living in
someone's memory. Written fresh on every run, describing the run it sits
in.
"""

from __future__ import annotations

from pathlib import Path

GLOSSARY_MD = "README.md"

COLUMN_GLOSSARY = """\
## What each column of `feature_stats.csv` means

### How many rows are behind the number

- **n_rows_in_file** - every row in the source file, whether or not this
  column has a value there. The same for every row of this table.
- **n_rows_with_a_value** - how many of those rows the source actually
  published a value for. Lower than `n_rows_in_file` means the Census
  suppressed it or could not estimate it, which at tract level happens
  where the relevant population is too small to publish.
- **pct_of_file_missing** - that shortfall, as a percent of the file.
- **n_rows_in_this_report** - how many rows THIS report describes. Under
  the model sample it is identical for every column, because the
  regression keeps only rows complete on every feature at once; under
  the native sample it varies by column.

### Where the values sit

- **mean** - arithmetic mean over the rows in this report.
- **weighted_mean** - mean weighted by Hispanic population. The models
  fit both weighted and unweighted, so a gap between this and the plain
  mean means the feature looks different in the places where Hispanic
  residents actually live.
- **sd** - standard deviation (sample, ddof=1).
- **sd_over_mean** - the coefficient of variation: `sd / mean`. Spread
  as a fraction of level, so features on different scales can be
  compared. Blank where the feature can go negative, because a mean near
  zero makes the ratio meaningless.
- **min**, **max** - smallest and largest value.
- **p5**, **q1**, **median**, **q3**, **p95** - the 5th, 25th, 50th,
  75th and 95th percentiles. More robust than min and max, which a
  single odd row can set.
- **range** - `max - min`.
- **iqr** - `q3 - q1`, the middle half's width.

### What shape they make

- **pct_zero** - percent of rows at exactly zero. Large for shares of a
  small subpopulation, and completely invisible in the mean.
- **pct_exactly_1** - percent of rows at exactly 1.0, the ceiling of a
  share (every Hispanic household on broadband, say). Blank for anything
  that is not a 0-to-1 share, where landing on 1 means nothing.
- **skew** - asymmetry; positive is a long right tail. Trees are
  indifferent to it, ridge is not.
- **n_unique** - distinct values. Far fewer than expected means the
  feature is near-constant in this geography.
- **spearman_with_...** - rank correlation with the outcome the heading
  names, over rows where both exist. Rank rather than linear, because
  these relationships are monotone but curved. The outcome is named in
  the heading so the table never leaves "target" to be guessed at.
"""


def write_glossary(output_dir: Path, scope_note: str, columns: list[str]) -> Path:
    """Write README.md explaining the stats table; return its path.

    Parameters
    ----------
    output_dir : Path
        The report directory.
    scope_note : str
        The same line the figures carry.
    columns : list of str
        The columns described, in table order.

    Returns
    -------
    Path
        The file written.
    """
    described = "\n".join(f"- `{column}`" for column in columns)
    text = (
        "# Feature report\n\n"
        f"{scope_note}\n\n"
        f"`feature_stats.csv` describes the {len(columns)} columns listed "
        "at the bottom. `distributions.png` puts all of them on one sheet; "
        "each `hist_<COLUMN>.png` is one of them alone.\n\n"
        "Every histogram title carries the formula the build actually "
        "computed, so a share states what it is a share OF.\n\n"
        f"{COLUMN_GLOSSARY}\n"
        f"## Columns described here\n\n{described}\n"
    )
    path = output_dir / GLOSSARY_MD
    path.write_text(text)
    return path
