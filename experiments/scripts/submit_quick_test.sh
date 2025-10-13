#!/bin/bash
# Batch experiment submission for: quick_test
# Generated on: 2025-10-13 15:02:16

EXPERIMENT_SET="quick_test"
SCRIPTS_DIR="/home/aless/PROJECTS/LLM-Needs-a-Plan/experiments/scripts"
LOGS_DIR="/home/aless/PROJECTS/LLM-Needs-a-Plan/experiments/logs"

echo "Starting batch submission for experiment set: $EXPERIMENT_SET"
echo "Total experiments: 2"

# Create batch log directory
BATCH_LOG_DIR="$LOGS_DIR/batch_$EXPERIMENT_SET"
mkdir -p "$BATCH_LOG_DIR"

# Job submission with dependency management
declare -a JOB_IDS
MAX_CONCURRENT=4
SUBMITTED=0


# Submit experiment: quick_test_phi4_tetris_tetris01
echo "Submitting job 1/2: quick_test_phi4_tetris_tetris01"

JOB_OUTPUT=$(sbatch "$SCRIPTS_DIR/quick_test_phi4_tetris_tetris01.sh")
if [ $? -eq 0 ]; then
    JOB_ID=$(echo "$JOB_OUTPUT" | grep -o '[0-9]\+')
    JOB_IDS+=($JOB_ID)
    echo "  Job ID: $JOB_ID"
    SUBMITTED=$((SUBMITTED + 1))
    
    # Wait if we've hit concurrent limit
    if [ $((SUBMITTED % MAX_CONCURRENT)) -eq 0 ] && [ $SUBMITTED -lt 2 ]; then
        echo "  Reached concurrent limit ($MAX_CONCURRENT), waiting for jobs to complete..."
        # Wait for any job to complete before submitting more
        squeue -u $USER --format="%.18i %.9P %.50j %.8u %.8T %.10M %.9l %.6D %R" | grep -E "$(IFS='|'; echo "${JOB_IDS[*]}")"
        sleep 30
    fi
else
    echo "  Failed to submit quick_test_phi4_tetris_tetris01"
fi

# Submit experiment: quick_test_phi4_tetris_tetris02
echo "Submitting job 2/2: quick_test_phi4_tetris_tetris02"

JOB_OUTPUT=$(sbatch "$SCRIPTS_DIR/quick_test_phi4_tetris_tetris02.sh")
if [ $? -eq 0 ]; then
    JOB_ID=$(echo "$JOB_OUTPUT" | grep -o '[0-9]\+')
    JOB_IDS+=($JOB_ID)
    echo "  Job ID: $JOB_ID"
    SUBMITTED=$((SUBMITTED + 1))
    
    # Wait if we've hit concurrent limit
    if [ $((SUBMITTED % MAX_CONCURRENT)) -eq 0 ] && [ $SUBMITTED -lt 2 ]; then
        echo "  Reached concurrent limit ($MAX_CONCURRENT), waiting for jobs to complete..."
        # Wait for any job to complete before submitting more
        squeue -u $USER --format="%.18i %.9P %.50j %.8u %.8T %.10M %.9l %.6D %R" | grep -E "$(IFS='|'; echo "${JOB_IDS[*]}")"
        sleep 30
    fi
else
    echo "  Failed to submit quick_test_phi4_tetris_tetris02"
fi

echo "Batch submission completed!"
echo "Submitted jobs: $SUBMITTED"
echo "Job IDs: ${JOB_IDS[@]}"

# Save job tracking info
echo "${JOB_IDS[@]}" > "$BATCH_LOG_DIR/job_ids.txt"
echo "Job IDs saved to: $BATCH_LOG_DIR/job_ids.txt"

# Show queue status
echo "Current queue status:"
squeue -u $USER
