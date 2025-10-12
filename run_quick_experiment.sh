#!/bin/bash
#SBATCH --account=IscrC_ArtLLMs
#SBATCH --partition=boost_usr_prod
#SBATCH --time=00:30:00
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --job-name=llm_quick_test
#SBATCH --output=quick_experiment_%j.out
#SBATCH --error=quick_experiment_%j.err

# ====================================================================
# Quick LLM-Needs-a-Plan Experiment (Single Problem Test)
# ====================================================================

echo "=========================================="
echo "Quick PDDL Planning Test"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start Time: $(date)"

# Setup environment
module load python/3.11.7
source project_venv/bin/activate
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Quick GPU check
nvidia-smi --query-gpu=name,memory.free --format=csv,noheader

echo "=========================================="
echo "Running Quick Test"
echo "=========================================="

# Run with minimal parameters - single iteration, one problem
python src/main.py \
    --domain tetris \
    --max_iterations 1 \
    --max_tokens 2000 \
    --verbose \
    --model phi4

RESULT=$?

echo "=========================================="
echo "Quick Test Results"
echo "=========================================="

if [ $RESULT -eq 0 ]; then
    echo "✓ QUICK TEST PASSED"
    echo "Ready for full experiments!"
else
    echo "✗ QUICK TEST FAILED"
    echo "Check configuration before running full experiment"
fi

echo "Check results in src/results/"
ls -la src/results/ 2>/dev/null || echo "No results directory found"

echo "End Time: $(date)"
exit $RESULT