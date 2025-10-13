#!/bin/bash
#SBATCH --account=IscrC_ArtLLMs
#SBATCH --partition=boost_usr_prod
#SBATCH --time=00:45:00
#SBATCH --gres=gpu:4
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=256G
#SBATCH --job-name=llm_single_test
#SBATCH --output=single_test_%j.out
#SBATCH --error=single_test_%j.err

# ====================================================================
# Single Problem LLM Test (For Memory-Constrained Testing)
# ====================================================================

echo "=========================================="
echo "Single Problem PDDL Planning Test"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start Time: $(date)"

# Setup environment
module load python/3.11.7
source project_venv/bin/activate
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Optimize CUDA memory management for Llama4 (107B model)
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_LAUNCH_BLOCKING=0
export TOKENIZERS_PARALLELISM=false

# Quick GPU check
nvidia-smi --query-gpu=name,memory.free --format=csv,noheader

echo "=========================================="
echo "Creating Limited Test Dataset"
echo "=========================================="

# Create a temporary test directory with just 3 problems
TEST_DIR="src/test_data"
mkdir -p "$TEST_DIR/tetris"

# Copy domain file
cp src/data/tetris/tetris_domain.pddl "$TEST_DIR/tetris/"

# Copy just the first 3 problem files
echo "Copying first 3 tetris problems for testing..."
ls src/data/tetris/*.pddl | grep -v domain | head -3 | while read file; do
    cp "$file" "$TEST_DIR/tetris/"
    echo "  Copied: $(basename $file)"
done

echo "=========================================="
echo "Running Limited Test"
echo "=========================================="

# Clear any existing GPU processes
echo "Clearing GPU memory..."
python3 -c "
import torch
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    print(f'Cleared GPU memory. Available: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
"

# Run with the limited test dataset
python src/main.py \
    --problems_path "$TEST_DIR" \
    --domain tetris \
    --max_iterations 1 \
    --max_tokens 1500 \
    --temperature 0.1 \
    --verbose \
    --model llama4

RESULT=$?

echo "=========================================="
echo "Single Problem Test Results"
echo "=========================================="

if [ $RESULT -eq 0 ]; then
    echo "✓ LIMITED TEST PASSED"
    echo "Llama4 can handle individual problems successfully"
    echo "The issue may be memory accumulation across multiple problems"
    
    echo ""
    echo "Recommendations:"
    echo "1. Use the new experiment framework with single-problem jobs"
    echo "2. Consider implementing memory cleanup between problems"
    echo "3. Use Phi4 model for batch processing of many problems"
else
    echo "✗ LIMITED TEST FAILED"
    echo "Check Llama4 model configuration and GPU resources"
fi

echo ""
echo "Test Results:"
ls -la src/results/ 2>/dev/null || echo "No results directory found"

# Cleanup test directory
echo "Cleaning up test directory..."
rm -rf "$TEST_DIR"

# Final GPU memory cleanup
echo "Final GPU memory cleanup..."
python3 -c "
import torch
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    print('GPU memory cleared')
"

echo "End Time: $(date)"
exit $RESULT