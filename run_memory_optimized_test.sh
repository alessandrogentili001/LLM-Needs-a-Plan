#!/bin/bash
#SBATCH --account=IscrC_ArtLLMs
#SBATCH --partition=boost_usr_prod
#SBATCH --time=00:45:00
#SBATCH --gres=gpu:4
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=256G
#SBATCH --job-name=llm_memory_optimized
#SBATCH --output=memory_test_%j.out
#SBATCH --error=memory_test_%j.err

# ====================================================================
# Memory-Optimized Llama4 Test
# ====================================================================

echo "=========================================="
echo "Memory-Optimized PDDL Planning Test"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start Time: $(date)"

# Setup environment
module load python/3.11.7
source project_venv/bin/activate
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Aggressive memory optimization settings
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:512
export CUDA_LAUNCH_BLOCKING=0
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8

# Pre-clear any GPU memory
echo "Pre-clearing GPU memory..."
python3 -c "
import torch
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        torch.cuda.set_device(i)
        torch.cuda.empty_cache()
    print('All GPU memory cleared')
"

# Detailed GPU status
echo "=========================================="
echo "GPU Memory Status"
echo "=========================================="
nvidia-smi --query-gpu=index,name,memory.total,memory.free,memory.used --format=csv,noheader,nounits

echo "=========================================="
echo "Creating Single Problem Test"
echo "=========================================="

# Create test with just ONE problem
TEST_DIR="src/single_test"
mkdir -p "$TEST_DIR/tetris"
cp src/data/tetris/tetris_domain.pddl "$TEST_DIR/tetris/"
ls src/data/tetris/*.pddl | grep -v domain | head -1 | while read file; do
    cp "$file" "$TEST_DIR/tetris/"
    echo "  Testing with: $(basename $file)"
done

echo "=========================================="
echo "Running Memory-Optimized Test"
echo "=========================================="

# Run with very conservative memory settings
python src/main.py \
    --problems_path "$TEST_DIR" \
    --domain tetris \
    --max_iterations 1 \
    --max_tokens 1000 \
    --temperature 0.0 \
    --verbose \
    --model llama4

RESULT=$?

echo "=========================================="
echo "Post-Test GPU Memory Status" 
echo "=========================================="
nvidia-smi --query-gpu=index,name,memory.total,memory.free,memory.used --format=csv,noheader,nounits

echo "=========================================="
echo "Test Results"
echo "=========================================="

if [ $RESULT -eq 0 ]; then
    echo "✅ MEMORY-OPTIMIZED TEST PASSED"
    echo "Llama4 can work with improved memory management"
else
    echo "❌ MEMORY-OPTIMIZED TEST FAILED"
    echo "Llama4 still has memory issues even with optimization"
fi

echo ""
echo "Generated results:"
ls -la src/results/ 2>/dev/null || echo "No results directory found"

# Cleanup
rm -rf "$TEST_DIR"

# Final memory report
echo ""
echo "Final GPU memory cleanup..."
python3 -c "
import torch
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        torch.cuda.set_device(i)
        torch.cuda.empty_cache()
    print('Final cleanup completed')
"

echo "End Time: $(date)"
exit $RESULT