#!/bin/bash
#SBATCH --job-name=quick_test_phi4_tetris_tetris02
#SBATCH --partition=boost_usr_prod
#SBATCH --account=cin_staff
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=256GB
#SBATCH --gres=gpu:1
#SBATCH --output=/leonardo_work/Pra24_5520/aless/LLM-Needs-a-Plan/experiments/logs/quick_test_phi4_tetris_tetris02_%j.out
#SBATCH --error=/leonardo_work/Pra24_5520/aless/LLM-Needs-a-Plan/experiments/logs/quick_test_phi4_tetris_tetris02_%j.err

# Experiment: quick_test_phi4_tetris_tetris02
# Model: phi4 (Phi4)
# Domain: tetris (Tetris)
# Problem: tetris02.pddl

echo "Starting experiment: quick_test_phi4_tetris_tetris02"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "GPUs: 1"

# Load modules
module purge
module load python/3.11.6
module load cuda/12.1

# Navigate to project directory
cd /leonardo_work/Pra24_5520/aless/LLM-Needs-a-Plan

# Activate virtual environment if available
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:/leonardo_work/Pra24_5520/aless/LLM-Needs-a-Plan/src"
export CUDA_VISIBLE_DEVICES=$(echo $CUDA_VISIBLE_DEVICES | tr ',' ' ' | cut -d' ' -f1-1 | tr ' ' ',')

# Create experiment-specific result directory
RESULT_DIR="/leonardo_work/Pra24_5520/aless/LLM-Needs-a-Plan/experiments/results/quick_test_phi4_tetris_tetris02"
mkdir -p "$RESULT_DIR"

# Run the experiment
python3 src/main.py \
    --model_path "src/models/Phi4" \
    --domain_file "src/problems/tetris/tetris-domain.pddl" \
    --problem_file "src/problems/tetris/tetris02.pddl" \
    --output_dir "$RESULT_DIR" \
    --temperature 0.1 \
    --max_tokens 2048 \
    --validate \
    --save_intermediate \
    --experiment_id "quick_test_phi4_tetris_tetris02"

# Check exit status
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "Experiment quick_test_phi4_tetris_tetris02 completed successfully"
    echo "Results saved to: $RESULT_DIR"
else
    echo "Experiment quick_test_phi4_tetris_tetris02 failed with exit code: $EXIT_CODE"
fi

echo "Job completed at: $(date)"
exit $EXIT_CODE
