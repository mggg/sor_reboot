from __future__ import annotations

import pandas as pd

from ...utils import config
from ...analysis import modeling, report

# SHAP dependence: the primary explanatory target + curated interaction pairs.
# interaction "auto" lets SHAP pick the strongest interacting feature.
DEPENDENCE_TARGET = "Hisp SOR Alone PL Percent"
DEPENDENCE_PAIRS = [
    ("log_SPANISHLIMENGLISH", "log_BACHDEG"),  # does education buffer the language effect?
    ("log_FOREIGNBORN", "log_NONCITIZENS"),
    ("log_MEXICANORIGIN", "auto"),
    ("MEDAGE", "auto"),
]


def run_shap_dependence(df_reg: pd.DataFrame, X_reg: pd.DataFrame) -> None:
    """SHAP dependence plots (explanatory feature interactions)."""
    config.DEPENDENCE_DIR.mkdir(parents=True, exist_ok=True)

    paths = modeling.shap_dependence_plots(
        df_reg, DEPENDENCE_TARGET, X_reg,
        pairs=DEPENDENCE_PAIRS, save_dir=config.DEPENDENCE_DIR,
    )
    print(f"  wrote {len(paths)} dependence plots -> {config.DEPENDENCE_DIR}")

    readme = config.DEPENDENCE_DIR / "README.md"
    body = (
        f"SHAP **dependence** plots for `{DEPENDENCE_TARGET}` — the RF is fit on the "
        "full data (explanatory, not scored). Each shows how a feature's SHAP "
        "contribution varies with that feature's value, colored by an interacting "
        "feature. `log_` features were log1p-transformed. To generate one per "
        "feature instead of this curated set, call `shap_dependence_plots(..., pairs=None)`.\n\n"
        + report.embed_figures(paths, readme.parent)
    )
    report.write_section_readme(readme, "SHAP dependence (interactions)", body)
    print(f"  wrote section summary -> {readme}")
