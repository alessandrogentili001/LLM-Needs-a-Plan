#!/bin/bash
#SBATCH --account=IscrC_ArtLLMs
#SBATCH --partition=boost_usr_prod
#SBATCH --time=10:00:00
#SBATCH --gres=gpu:4
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=256G
#SBATCH --job-name=llama4_final_test
#SBATCH --output=llama4_final_%j.out
#SBATCH --error=llama4_final_%j.err

# ====================================================================
# Final Llama4 Test with Maximum Memory Optimization
# ====================================================================

echo "=========================================="
echo "Final Llama4 Memory Optimization Test"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start Time: $(date)"

# Setup environment
module load python/3.11.7
source project_venv/bin/activate
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Maximum memory optimization
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:256
export CUDA_LAUNCH_BLOCKING=0
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=4

echo "Applied optimizations:"
echo "  - FP16 precision instead of BF16"
echo "  - 15GB reserved per GPU for inference (up from 10GB)" 
echo "  - Disabled KV cache during generation"
echo "  - No beam search"
echo "  - Aggressive memory fragmentation control"

# Pre-clear memory
python3 -c "
import torch
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        torch.cuda.set_device(i)
        torch.cuda.empty_cache()
    print('GPU memory cleared')
"

echo "=========================================="
echo "GPU Memory Status (Before)"
echo "=========================================="
nvidia-smi --query-gpu=index,name,memory.total,memory.free,memory.used --format=csv,noheader,nounits

# Create minimal test
TEST_DIR="src/final_test"
mkdir -p "$TEST_DIR/tetris"
cp src/data/tetris/tetris_domain.pddl "$TEST_DIR/tetris/"
ls src/data/tetris/*.pddl | grep -v domain | head -1 | while read file; do
    cp "$file" "$TEST_DIR/tetris/"
    echo "Testing: $(basename $file)"
done

echo "=========================================="
echo "Running Final Llama4 Test"
echo "=========================================="

# Run with maximum memory efficiency
python src/main.py \
    --problems_path "$TEST_DIR" \
    --domain tetris \
    --max_iterations 1 \
    --max_tokens 800 \
    --temperature 0.0 \
    --verbose \
    --model llama4

RESULT=$?

echo "=========================================="
echo "GPU Memory Status (After)"
echo "=========================================="
nvidia-smi --query-gpu=index,name,memory.total,memory.free,memory.used --format=csv,noheader,nounits

echo "=========================================="
echo "Final Test Results"
echo "=========================================="

if [ $RESULT -eq 0 ]; then
    echo "🎉 SUCCESS! Llama4 works with extreme memory optimization"
    echo ""
    echo "Working configuration:"
    echo "  ✅ FP16 precision"
    echo "  ✅ 49GB per GPU for model (15GB reserved)"
    echo "  ✅ No KV cache during generation"
    echo "  ✅ Single beam generation"
    echo "  ✅ 800 token limit"
    echo ""
    echo "🚀 You can now use Llama4 for experiments with these settings!"
else
    echo "❌ Llama4 still fails with maximum optimization"
    echo ""
    echo "🎯 STRONG RECOMMENDATION: Switch to Phi4"
    echo "   Reasons:"
    echo "   - Phi4: 14B parameters vs Llama4: 8B parameters"
    echo "   - Phi4: 1 GPU (32GB) vs Llama4: 1 GPU (20GB)"
    echo "   - Phi4: Better reasoning capabilities"
    echo "   - Phi4: Optimized for planning tasks"
    echo ""
    echo "   Or consider Gemma3 (27B) for maximum performance."
    echo "   Performance comparison studies show Phi4 often"
    echo "   matches or exceeds Llama4 on complex reasoning tasks."
fi

echo ""
echo "Generated results:"
find src/results -name "*.txt" -newer "$TEST_DIR" 2>/dev/null

# Cleanup
rm -rf "$TEST_DIR"

echo ""
echo "💡 Next Steps:"
if [ $RESULT -eq 0 ]; then
    echo "   1. Use the new experiment framework with Llama4"
    echo "   2. Apply the same memory settings to production jobs"
else
    echo "   1. Switch to Phi4: --model phi4"
    echo "   2. Test Phi4: sbatch run_phi4_alternative.sh"  
    echo "   3. Use experiment framework with Phi4"
fi

echo "End Time: $(date)"
exit $RESULT