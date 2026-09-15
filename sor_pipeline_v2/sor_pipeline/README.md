# SOR Pipeline

This pipeline is the refactor of the original SOR repo's three analysis notebooks
(`3hispaniccleanjune.ipynb`, `statetractcleanedjune.ipynb`, and
`nationhispanicracepredictionjune.ipynb`). The original repo's ecological inference
work (`prediction/` folder) was never completed and is not migrated here.

**`run_national.py`** covers the county-level descriptive notebook: it ingests and
merges 2020 Decennial PL, ACS, TIGER geometry, and election data (`ingest/`,
`clean/`), then runs scatter figures, Pearson correlations, spatial analysis
(Moran's I and CAPY half-edge), and univariate logistic regressions
(`runners/national/`, algorithms in `analysis/`).

**`run_tract.py`** is the tract-level twin, run per state (CA/TX/FL/NY) with a
`--state` flag, reusing the same shared modules with state-specific clustering
thresholds (`TRACT_MIN_POP` in config).

**`run_prediction.py`** covers the predictive-modeling notebook: dominant-race
classification (baseline / L1 logistic / random forest), random-forest regression on
within-Hispanic proportions with SHAP, SHAP dependence plots, and the alternative
Lasso and log-ratio regressors (`runners/prediction/`, models in
`analysis/modeling.py`). It reads the dataset `run_national` builds.

## How to Run

Create a virtual environment (Python 3.11) and install the dependencies:

```
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then, from the `sor_reboot/` directory:

```
python -m sor_pipeline.run_national               # county-level descriptive pipeline
python -m sor_pipeline.run_tract                  # tract-level, all four states
python -m sor_pipeline.run_tract --state CA       # tract-level, one state
python -m sor_pipeline.run_prediction             # predictive modeling
```

Order matters once: `run_prediction` reads the dataset that `run_national`'s first
step produces, so `run_national` must have completed its dataset build at least
once. `run_tract` is independent — it builds its own per-state datasets.

Fetching Census data requires a Census API key in the `CENSUS_API_KEY` environment
variable, loaded from a `.env` file. **You must specify the path to your `.env` file
in `utils/config.py`**: the `load_dotenv(...)` call near the top of that file takes
the path as its argument, and it is currently hardcoded to an absolute path on the
original author's machine (pointing at the old repo). Edit that path to point at
your own `.env` file — or export `CENSUS_API_KEY` in your shell, which works
regardless of the dotenv path. The pipeline raises a clear error if the key is
missing (the notebooks would fail silently instead).

Every expensive step is checkpointed: if its output already exists on disk, the
driver asks before re-running it (defaulting to no), so re-runs skip API calls and
finished analyses unless told otherwise. In a non-interactive shell, existing
outputs are kept automatically. Outputs land under `sor_pipeline/data/`:
`national/` (with analysis outputs in a subdirectory named for the run's parameters,
e.g. `excl-60-66-69-78_minpop-36/`), `tract/<STATE>/`, and `prediction/`. Each
analysis section writes a `README.md` collecting its tables and figures, so the data
tree is browsable without rerunning anything.
