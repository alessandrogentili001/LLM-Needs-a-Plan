#!/bin/bash
#SBATCH --account=IscrC_ArtLLMs
#SBATCH --partition=boost_usr_prod
#SBATCH --time=00:30:00
#SBATCH --gres=gpu:4
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --job-name=llm_needs_plan_cluster_test
#SBATCH --output=cluster_test_%j.out
#SBATCH --error=cluster_test_%j.err

# ====================================================================
# LLM-Needs-a-Plan Cluster Test Job
# ====================================================================

echo "=========================================="
echo "Job Information"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Job Name: $SLURM_JOB_NAME"
echo "Node: $SLURM_NODELIST"
echo "Account: $SLURM_JOB_ACCOUNT"
echo "Partition: $SLURM_JOB_PARTITION"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory: $SLURM_MEM_PER_NODE MB"
echo "GPU: $SLURM_GPUS"
echo "Start Time: $(date)"
echo "=========================================="

# Load required modules
echo "Loading Python module..."
module load python/3.11.7

# Check if we're in the right directory (look for src folder and config.yml)
if [ ! -d "src" ] || [ ! -f "config.yml" ]; then
    echo "ERROR: Not in LLM-Needs-a-Plan project directory!"
    echo "Current directory: $(pwd)"
    echo "Looking for 'src' directory and 'config.yml' file"
    echo "Available files and directories:"
    ls -la
    exit 1
fi

echo "Working directory: $(pwd)"

# Activate virtual environment (check for both venv and project_venv)
if [ -d "venv" ]; then
    VENV_DIR="venv"
elif [ -d "project_venv" ]; then
    VENV_DIR="project_venv"
else
    echo "ERROR: Virtual environment not found!"
    echo "Looking for 'venv' or 'project_venv' directory"
    echo "Available directories:"
    ls -la
    exit 1
fi

echo "Activating virtual environment: $VENV_DIR"
source $VENV_DIR/bin/activate

# Verify Python environment
echo "Python executable: $(which python)"
echo "Python version: $(python --version)"

# Check GPU availability
echo "=========================================="
echo "GPU Information"
echo "=========================================="
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader
else
    echo "nvidia-smi not available"
fi

# Set up Python path for imports
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
echo "Python path set to: $PYTHONPATH"

# Set project root environment variable for the test script
export LLM_PROJECT_ROOT="$(pwd)"
echo "Project root set to: $LLM_PROJECT_ROOT"

# Verify key paths exist
echo "Verifying project structure..."
echo "  src directory: $([ -d src ] && echo "✓ EXISTS" || echo "✗ MISSING")"
echo "  src/data directory: $([ -d src/data ] && echo "✓ EXISTS" || echo "✗ MISSING")"
echo "  config.yml: $([ -f config.yml ] && echo "✓ EXISTS" || echo "✗ MISSING")"

# Verify dependencies are installed
echo "Checking key dependencies..."
python -c "
try:
    import torch
    print('✓ PyTorch:', torch.__version__)
except ImportError:
    print('✗ PyTorch: NOT FOUND - run: pip install torch>=2.1.0')

try:
    import transformers
    print('✓ Transformers:', transformers.__version__)
except ImportError:
    print('✗ Transformers: NOT FOUND - run: pip install transformers==4.41.2')
"

# Run the cluster test suite
echo "=========================================="
echo "Running Test Suite"
echo "=========================================="

# Run tests and capture exit code
python src/tests/test_cluster.py

TEST_EXIT_CODE=$?

echo "=========================================="
echo "Job Summary"
echo "=========================================="
echo "Test exit code: $TEST_EXIT_CODE"
echo "End time: $(date)"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ ALL TESTS PASSED"
else
    echo "✗ SOME TESTS FAILED"
fi

echo "Check output files:"
echo "  Output: cluster_test_${SLURM_JOB_ID}.out"
echo "  Errors: cluster_test_${SLURM_JOB_ID}.err"

exit $TEST_EXIT_CODE