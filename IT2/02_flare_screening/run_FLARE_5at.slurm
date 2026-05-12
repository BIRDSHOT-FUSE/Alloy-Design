#!/bin/bash
##ENVIRONMENT SETTINGS; CHANGE WITH CAUTION
#SBATCH --export=NONE                #Do not propagate environment

##NECESSARY JOB SPECIFICATIONS
#SBATCH --job-name=FLARE_chunked
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=48
#SBATCH --mem=240G
#SBATCH --output=OUT_FLARE_chunked.%A_%a
#SBATCH --account=132743716365

##ARRAY SPECIFICATION — 100 chunks (override with: sbatch --array=0-N ...)
#SBATCH --array=0-99

##OPTIONAL JOB SPECIFICATIONS
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=ifadasamuel@tamu.edu

# ---------------------------------------------------------------------------
# USAGE: This SLURM file runs ONE decay time per submission, to keep SU
# reservations small (so the submission fits within the account balance).
# Pass the decay name as a positional arg:
#
#     sbatch run_FLARE_5at.slurm 1sec
#     sbatch run_FLARE_5at.slurm 1month
#     sbatch run_FLARE_5at.slurm 100yr
#
# If no arg is given, defaults to 1sec.
#
# After ALL array tasks for a given decay finish, you can stitch:
#     python stitch_flare.py --decay 1sec  --expected 100
# Or stitch all three after they're all done:
#     python stitch_flare.py --expected 100
# ---------------------------------------------------------------------------

DECAY="${1:-1sec}"
case "$DECAY" in
    1sec|1month|100yr) ;;
    *)
        echo "ERROR: DECAY must be one of: 1sec, 1month, 100yr (got: $DECAY)"
        exit 1
        ;;
esac

# ---------------------------------------------------------------------------
# Environment setup — uses the conda-based nimplex_env (FLARE is installed there too)
# ---------------------------------------------------------------------------
module purge
module load Mamba/23.11.0-0
source activate nimplex_env

export PATH=$CONDA_PREFIX/bin:$PATH
export NIMBLE_DIR=/scratch/user/ifadasamuel/.nimble
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH

cd $SLURM_SUBMIT_DIR

# Helpful diagnostic output (top of the .out file)
echo "=========================================="
echo "Array Job:   $SLURM_ARRAY_JOB_ID"
echo "Array Task:  $SLURM_ARRAY_TASK_ID of $SLURM_ARRAY_TASK_COUNT"
echo "Job ID:      $SLURM_JOB_ID"
echo "Decay:       $DECAY"
echo "Node:        $(hostname)"
echo "Started at:  $(date)"
echo "Working dir: $(pwd)"
echo "Python:      $(which python)"
echo "Tasks:       $SLURM_NTASKS"
echo "=========================================="

# ---------------------------------------------------------------------------
# RUN ONLY THE REQUESTED DECAY TIME
# Each array task processes its share (chunk #SLURM_ARRAY_TASK_ID of
# #SLURM_ARRAY_TASK_COUNT) of the ndiv=20 (5 at%) composition CSV.
# Output goes to flareFile/${DECAY}/. After all array tasks complete, run
# stitch_flare.py to merge per-chunk outputs into the final response file.
# ---------------------------------------------------------------------------

echo ""
echo "----- Running ${DECAY} decay (chunk $SLURM_ARRAY_TASK_ID) -----"
echo "Started: $(date)"
python "run_FLARE_${DECAY}_5at.py"

echo "=========================================="
echo "Array task $SLURM_ARRAY_TASK_ID ($DECAY) finished at: $(date)"
echo "=========================================="