#!/bin/bash
#SBATCH --job-name=temperature_sensitivity_analysis
#SBATCH --partition=boost_usr_prod
#SBATCH --account=IscrC_ArtLLMs
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64GB
#SBATCH --gres=gpu:1
#SBATCH --output=temperature_analysis_%j.out
#SBATCH --error=temperature_analysis_%j.err

# Temperature Sensitivity Analysis - Phi4 Planning
# Single SLURM script to run all temperature experiments

set -e

echo "🌡️ Starting Temperature Sensitivity Analysis"
echo "=============================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "Start time: $(date)"
echo ""

# Setup paths
PROJECT_ROOT="/leonardo_work/IscrC_ArtLLMs/aless/LLM-Needs-a-Plan"
RESULTS_DIR="$PROJECT_ROOT/experiments/results/temperature_analysis_$(date +%Y%m%d_%H%M%S)"
DATA_DIR="$PROJECT_ROOT/src/data"

# Create results directory
mkdir -p "$RESULTS_DIR/raw_results"
mkdir -p "$RESULTS_DIR/logs"

cd "$PROJECT_ROOT"

echo "📁 Results directory: $RESULTS_DIR"
echo ""

# Temperature values to test
TEMPERATURES=(0.0 0.1 0.3 0.5 0.7 0.9)

# Tetris problems
TETRIS_PROBLEMS=("tetris01.pddl" "tetris02.pddl" "tetris03.pddl")

# Load conda environment (if needed)
source ~/.bashrc
# conda activate your_environment_name  # Uncomment and adjust if using conda

# Run experiments
TOTAL_EXPERIMENTS=$((${#TEMPERATURES[@]} * ${#TETRIS_PROBLEMS[@]}))
CURRENT_EXP=0

echo "🔬 Running $TOTAL_EXPERIMENTS temperature experiments..."
echo ""

for temp in "${TEMPERATURES[@]}"; do
    echo "🌡️ Temperature: $temp"
    
    for problem in "${TETRIS_PROBLEMS[@]}"; do
        CURRENT_EXP=$((CURRENT_EXP + 1))
        echo "  📄 Problem $CURRENT_EXP/$TOTAL_EXPERIMENTS: $problem"
        
        # Create result file name
        RESULT_FILE="$RESULTS_DIR/raw_results/temp_${temp}_tetris_${problem}_results.json"
        LOG_FILE="$RESULTS_DIR/logs/temp_${temp}_tetris_${problem}.log"
        
        echo "    🚀 Starting experiment..." > "$LOG_FILE"
        echo "    Temperature: $temp" >> "$LOG_FILE"
        echo "    Problem: $problem" >> "$LOG_FILE"
        echo "    Start time: $(date)" >> "$LOG_FILE"
        
        # Run the experiment
        python3 "$PROJECT_ROOT/src/main.py" \
            --domain "$DATA_DIR/tetris-domain.pddl" \
            --problem "$DATA_DIR/$problem" \
            --model "Phi4" \
            --model_path "$PROJECT_ROOT/src/models/Phi4" \
            --temperature "$temp" \
            --max_new_tokens 5000 \
            --top_p 0.9 \
            --top_k 50 \
            --repetition_penalty 1.0 \
            --output "$RESULT_FILE" \
            --validate \
            --log_level INFO \
            2>> "$LOG_FILE"
        
        if [ $? -eq 0 ]; then
            echo "    ✅ Experiment completed successfully" | tee -a "$LOG_FILE"
        else
            echo "    ❌ Experiment failed" | tee -a "$LOG_FILE"
        fi
        
        echo "    End time: $(date)" >> "$LOG_FILE"
        echo ""
    done
done

echo ""
echo "📊 Temperature Analysis Complete!"
echo "================================="
echo "Total experiments: $TOTAL_EXPERIMENTS"
echo "Results directory: $RESULTS_DIR"
echo "End time: $(date)"

# Create experiment summary
cat > "$RESULTS_DIR/experiment_summary.json" << EOF
{
    "experiment_info": {
        "title": "Temperature Sensitivity Analysis for Phi4 Planning",
        "job_id": "$SLURM_JOB_ID",
        "start_time": "$(date -Iseconds)",
        "node": "$SLURMD_NODENAME"
    },
    "configuration": {
        "temperatures": [$(IFS=,; echo "${TEMPERATURES[*]}")],
        "problems": ["$(IFS='","'; echo "${TETRIS_PROBLEMS[*]}")"],
        "model": "Phi4",
        "domain": "tetris",
        "total_experiments": $TOTAL_EXPERIMENTS
    },
    "paths": {
        "results_directory": "$RESULTS_DIR",
        "raw_results": "$RESULTS_DIR/raw_results",
        "logs": "$RESULTS_DIR/logs"
    }
}
EOF

echo ""
echo "📈 To analyze results:"
echo "python3 $PROJECT_ROOT/experiments/temperature_analyzer.py $RESULTS_DIR"
echo ""
echo "🎯 Temperature sensitivity analysis completed!"