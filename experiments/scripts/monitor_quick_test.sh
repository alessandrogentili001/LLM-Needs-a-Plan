#!/bin/bash
# Experiment monitoring script for: quick_test

EXPERIMENT_SET="quick_test"
LOGS_DIR="/home/aless/PROJECTS/LLM-Needs-a-Plan/experiments/logs"
RESULTS_DIR="/home/aless/PROJECTS/LLM-Needs-a-Plan/experiments/results"
BATCH_LOG_DIR="$LOGS_DIR/batch_$EXPERIMENT_SET"

echo "=== Experiment Set: $EXPERIMENT_SET ==="
echo "Monitor started at: $(date)"
echo

# Check if batch log exists
if [ ! -f "$BATCH_LOG_DIR/job_ids.txt" ]; then
    echo "No batch job tracking found for $EXPERIMENT_SET"
    echo "Run generate_experiments.py first to create experiments"
    exit 1
fi

# Read job IDs
JOB_IDS=($(cat "$BATCH_LOG_DIR/job_ids.txt"))
echo "Tracking ${#JOB_IDS[@]} jobs"

# Show queue status
echo "=== Queue Status ==="
squeue -u $USER --format="%.18i %.9P %.50j %.8u %.8T %.10M %.9l %.6D %R"
echo

# Count job states
RUNNING=0
PENDING=0
COMPLETED=0
FAILED=0

for JOB_ID in "${JOB_IDS[@]}"; do
    STATUS=$(squeue -j $JOB_ID -h -o "%T" 2>/dev/null)
    if [ -z "$STATUS" ]; then
        # Job not in queue, check if it completed
        if sacct -j $JOB_ID -n -o State | grep -q "COMPLETED"; then
            COMPLETED=$((COMPLETED + 1))
        else
            FAILED=$((FAILED + 1))
        fi
    else
        case $STATUS in
            "RUNNING") RUNNING=$((RUNNING + 1)) ;;
            "PENDING") PENDING=$((PENDING + 1)) ;;
        esac
    fi
done

echo "=== Job Summary ==="
echo "Running: $RUNNING"
echo "Pending: $PENDING" 
echo "Completed: $COMPLETED"
echo "Failed: $FAILED"
echo "Total: ${#JOB_IDS[@]}"
echo

# Show recent completions
echo "=== Recent Results ==="
find "$RESULTS_DIR" -name "*quick_test*" -type d -mtime -1 | head -5 | while read result_dir; do
    exp_name=$(basename "$result_dir")
    if [ -f "$result_dir/experiment_results.json" ]; then
        echo "✓ $exp_name - Results available"
    else
        echo "⏳ $exp_name - In progress"
    fi
done

echo
echo "Monitor completed at: $(date)"
