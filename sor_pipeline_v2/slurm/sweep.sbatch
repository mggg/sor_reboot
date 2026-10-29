#!/bin/bash
# One group-stability run on the DDRI node. Every argument is passed through
# to `python -m regression.group_stability`, so one script serves every run:
#
#   sbatch --job-name=sor-tracts slurm/sweep.sbatch --level national_tracts --seeds 1 50
#
# Submit from sor_pipeline_v2/ (slurm/submit_group_stability_runs.sh does): the job finds
# the code through $SLURM_SUBMIT_DIR, so no path on the cluster is hardcoded.

#SBATCH --partition=DDRI
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=1-00:00:00
#SBATCH --output=slurm/logs/%x_%j.out

set -euo pipefail

# Both tree libraries default to every core they can see; on a shared
# 768-CPU node that is far more than this job was given.
export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"     # LightGBM
export LOKY_MAX_CPU_COUNT="$SLURM_CPUS_PER_TASK"  # scikit-learn's random forest
# Single-threaded OpenBLAS, and 8 CPUs above: at 32 CPUs, LightGBM and
# ridge crawled or returned NaN on q001's AMD EPYC 9965; the runs that
# completed cleanly used these settings.
export OPENBLAS_NUM_THREADS=1                     # numpy's linear algebra (ridge)
export MPLBACKEND=Agg                             # compute nodes have no display

echo "job $SLURM_JOB_ID ($SLURM_JOB_NAME) on $(hostname), $SLURM_CPUS_PER_TASK CPUs"
echo "started $(date)"
# The commit the results came from, so a figure can be traced to its code.
echo "commit $(git -C "$SLURM_SUBMIT_DIR" rev-parse HEAD 2>/dev/null || echo 'not a git checkout')"
echo "args: $*"

# The package imports from sor_pipeline_v2/, so that is where Python starts.
cd "$SLURM_SUBMIT_DIR"
uv run --frozen python -m regression.group_stability "$@"

echo "finished $(date)"
