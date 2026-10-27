#!/bin/bash
# Submit the county-grouped group-stability runs, one Slurm job each.
# Same scopes as submit_group_stability_runs.sh, but every train/test split
# keeps a county's tracts together (--split-grouping county), so each model
# is scored on counties it never trained on.
#
#   bash slurm/submit_county_grouped_runs.sh test   # one Georgia seed, to check the setup
#   bash slurm/submit_county_grouped_runs.sh        # every run below
#
# Each run writes to its own directory under
# sor_pipeline_v2/data/prediction/regression/, named for its flags
# (e.g. ..._tracts-GA_grouped-by-county_without-geography).

set -euo pipefail

# Run from sor_pipeline_v2/ wherever this was called from: sweep.sbatch
# finds the code through the directory it was submitted from.
cd "$(dirname "$0")/.."
mkdir -p slurm/logs  # Slurm will not create the log directory itself

# Every run below: county-grouped split, plus the full matrix without
# geography, so each run also answers whether location adds anything on
# top of the other features.
COUNTY_GROUPED=(--level national_tracts --split-grouping county --exclude geography)

# 8 CPUs and single-threaded OpenBLAS: at sweep.sbatch's default 32 CPUs,
# LightGBM and ridge crawled or returned NaN on q001's AMD EPYC 9965; the
# runs that completed cleanly used these settings.
export OPENBLAS_NUM_THREADS=1  # sbatch passes the submitting shell's environment to the job

submit() {
    local name="$1"
    shift
    sbatch --cpus-per-task=8 --job-name="$name" slurm/sweep.sbatch "${COUNTY_GROUPED[@]}" "$@"
}

if [[ "${1:-}" == "test" ]]; then
    submit sor-county-grouped-test --states 13 --seeds 1 1 --groups full
    exit 0
fi

# Main result.
submit sor-tracts-cg --seeds 1 50

# Within-state checks: the same 10 states as the tract-split runs.
submit sor-tracts-CA-cg --states 06 --seeds 1 50
submit sor-tracts-TX-cg --states 48 --seeds 1 50
submit sor-tracts-FL-cg --states 12 --seeds 1 50
submit sor-tracts-NY-cg --states 36 --seeds 1 50
submit sor-tracts-IL-cg --states 17 --seeds 1 50
submit sor-tracts-AZ-cg --states 04 --seeds 1 50
submit sor-tracts-NJ-cg --states 34 --seeds 1 50
submit sor-tracts-CO-cg --states 08 --seeds 1 50
submit sor-tracts-GA-cg --states 13 --seeds 1 50
submit sor-tracts-NC-cg --states 37 --seeds 1 50

# Hyperparameter sensitivity, national only, one setting moved at a time
# from the defaults: do the conclusions hold? A check, not a search --
# nothing here is picked by its test score.
# Depth: mostly the forest's knob; LightGBM's 31-leaf cap binds before
# depth 8 would, so only depth 4 constrains it.
submit sor-tracts-cg-depth4 --seeds 1 20 --max-depth 4
submit sor-tracts-cg-depth12 --seeds 1 20 --max-depth 12
# Tree count: smooths the forest; more boosting rounds for LightGBM.
submit sor-tracts-cg-trees300 --seeds 1 20 --n-estimators 300
# Leaves: LightGBM's own size cap.
submit sor-tracts-cg-leaves15 --seeds 1 20 --num-leaves 15
submit sor-tracts-cg-leaves63 --seeds 1 20 --num-leaves 63
# Slower learning with twice the rounds: same total fit, smaller steps.
submit sor-tracts-cg-lr05 --seeds 1 20 --learning-rate 0.05 --n-estimators 200
