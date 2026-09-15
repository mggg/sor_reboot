"""Write per-section README.md summaries: auto-generated tables + figure embeds,
with a hand-editable `## Notes` section that survives reruns.

The driver owns WHAT goes in each section (it has the data); this module owns the
mechanics of rendering markdown and not clobbering the human-written notes.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd

NOTES_HEADER = "## Notes"
NOTES_PLACEHOLDER = "_Write custom notes here (persists across reruns)!_"


def df_to_md(df: pd.DataFrame, index_label: str = "") -> str:
    """Render a DataFrame as a GitHub-flavored markdown table (floats to 3 dp)."""
    cols = [index_label] + [str(c) for c in df.columns]
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = []
    for idx, row in df.iterrows():
        cells = [str(idx)] + [
            f"{v:.3f}" if isinstance(v, float) else str(v) for v in row
        ]
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep] + rows)


def embed_figures(fig_paths: list[Path], readme_dir: Path) -> str:
    """Markdown image embeds, paths made relative to where the README lives."""
    return "\n".join(
        f"![{p.stem}]({p.relative_to(readme_dir).as_posix()})\n" for p in fig_paths
    )


def _existing_notes(path: Path) -> str:
    """Pull the text under `## Notes` from an existing README, else a placeholder."""
    if path.exists():
        text = path.read_text()
        if NOTES_HEADER in text:
            return text.split(NOTES_HEADER, 1)[1].strip()
    return NOTES_PLACEHOLDER


def write_section_readme(path: Path, title: str, body: str) -> None:
    """Write `# title` + auto-generated `body` + preserved `## Notes` to README.md."""
    notes = _existing_notes(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body}\n\n{NOTES_HEADER}\n\n{notes}\n")
