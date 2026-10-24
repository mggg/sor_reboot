#!/bin/bash
# Submit every group-stability run, one Slurm job each.
#
#   bash slurm/submit_group_stability_runs.sh test   # one county seed, to check the setup
#   bash slurm/submit_group_stability_runs.sh        # every run below
#
# Each run writes to its own directory under
# sor_pipeline_v2/data/prediction/regression/, named for its flags.

set -euo pipefail

# Run from sor_pipeline_v2/ wherever this was called from: sweep.sbatch
# finds the code through the directory it was submitted from.
cd "$(dirname "$0")/.."
mkdir -p slurm/logs  # Slurm will not create the log directory itself

submit() {
    local name="$1"
    shift
    sbatch --job-name="$name" slurm/sweep.sbatch "$@"
}

if [[ "${1:-}" == "test" ]]; then
    submit sor-test --level national_counties --seeds 1 1
    exit 0
fi

# Main result.
submit sor-tracts --level national_tracts --seeds 1 50

# Small-population ladder. The percents are cut on the complete-case
# tracts, which keep the smallest tracts out at these minimum Hispanic
# populations: top 93% -> >=103, top 75% -> >=248, top 53% -> >=502.
submit sor-tracts-min100 --level national_tracts --seeds 1 50 --top-percent 93
submit sor-tracts-min250 --level national_tracts --seeds 1 50 --top-percent 75
submit sor-tracts-min500 --level national_tracts --seeds 1 50 --top-percent 53

# The fully aggregated rung.
submit sor-counties --level national_counties --seeds 1 50

# Within-state checks: the 10 states with the most Hispanic residents.
# Puerto Rico (5th by count) is left out: it has no presidential returns
# and no ACS mobility or foreign-born-entry figures, so none of its tracts
# are complete cases. Each needs its own tract build,
# e.g. `python -m build_dataset.main_build --level national_tracts --states 48`.
submit sor-tracts-CA --level national_tracts --states 06 --seeds 1 50
submit sor-tracts-TX --level national_tracts --states 48 --seeds 1 50
submit sor-tracts-FL --level national_tracts --states 12 --seeds 1 50
submit sor-tracts-NY --level national_tracts --states 36 --seeds 1 50
submit sor-tracts-IL --level national_tracts --states 17 --seeds 1 50
submit sor-tracts-AZ --level national_tracts --states 04 --seeds 1 50
submit sor-tracts-NJ --level national_tracts --states 34 --seeds 1 50
submit sor-tracts-CO --level national_tracts --states 08 --seeds 1 50
submit sor-tracts-GA --level national_tracts --states 13 --seeds 1 50
submit sor-tracts-NC --level national_tracts --states 37 --seeds 1 50

# Hyperparameter sensitivity: deeper trees for both tree models.
submit sor-tracts-depth12 --level national_tracts --seeds 1 20 --max-depth 12
