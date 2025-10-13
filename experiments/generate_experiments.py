#!/usr/bin/env python3
"""
LLM-Needs-a-Plan Experiment Generator

This script generates individual SLURM job scripts for experiments defined in the configuration.
It creates systematic experiments combining models, domains, and problems according to the
experiment sets specified in experiment_config.yml.
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import json


class ExperimentGenerator:
    def __init__(self, config_path: str, base_dir: str = None):
        """Initialize the experiment generator."""
        self.config_path = Path(config_path)
        self.base_dir = Path(base_dir) if base_dir else self.config_path.parent.parent
        
        # Load configuration
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Create output directories - fix nested path issue
        if "experiments" in str(self.base_dir).split('/')[-1]:
            # If base_dir is already experiments directory
            self.scripts_dir = self.base_dir / "scripts"
            self.results_dir = self.base_dir / "results" 
            self.logs_dir = self.base_dir / "logs"
        else:
            # If base_dir is project root
            self.scripts_dir = self.base_dir / "experiments" / "scripts"
            self.results_dir = self.base_dir / "experiments" / "results" 
            self.logs_dir = self.base_dir / "experiments" / "logs"
        
        for directory in [self.scripts_dir, self.results_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def generate_experiment_matrix(self, experiment_set: str) -> List[Dict[str, Any]]:
        """Generate all experiment combinations for a given experiment set."""
        if experiment_set not in self.config['experiment_sets']:
            raise ValueError(f"Unknown experiment set: {experiment_set}")
        
        exp_config = self.config['experiment_sets'][experiment_set]
        models = exp_config['models']
        domains = exp_config['domains']
        problem_limit = exp_config.get('problem_limit')
        
        experiments = []
        
        for model_name in models:
            for domain_name in domains:
                model_config = self.config['models'][model_name]
                domain_config = self.config['domains'][domain_name]
                
                # Get problems for this domain
                problems = domain_config['problems']
                if problem_limit:
                    problems = problems[:problem_limit]
                
                for problem_file in problems:
                    experiment = {
                        'id': f"{experiment_set}_{model_name}_{domain_name}_{problem_file.split('.')[0]}",
                        'model': model_name,
                        'domain': domain_name,
                        'problem': problem_file,
                        'model_config': model_config,
                        'domain_config': domain_config,
                        'exp_set': experiment_set,
                        'priority': exp_config['priority']
                    }
                    experiments.append(experiment)
        
        return experiments
    
    def generate_slurm_script(self, experiment: Dict[str, Any]) -> str:
        """Generate SLURM job script for a single experiment."""
        exp_id = experiment['id']
        model_config = experiment['model_config']
        
        # GPU configuration
        gpus = model_config['gpus']
        gpu_directive = f"#SBATCH --gres=gpu:{gpus}" if gpus > 0 else ""
        
        # Time limit based on model size
        if model_config['size'] == "107B":
            time_limit = "04:00:00"  # Longer for large models
        else:
            time_limit = self.config['global']['cluster']['time_limit']
        
        # Paths
        base_dir = self.config['global']['paths']['base_dir']
        results_dir = self.config['global']['paths']['results_dir']
        logs_dir = self.config['global']['paths']['logs_dir']
        
        script_content = f"""#!/bin/bash
#SBATCH --job-name={exp_id}
#SBATCH --partition={self.config['global']['cluster']['partition']}
#SBATCH --account={self.config['global']['cluster']['account']}
#SBATCH --time={time_limit}
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task={self.config['global']['cluster']['cpus']}
#SBATCH --mem={self.config['global']['cluster']['memory']}
{gpu_directive}
#SBATCH --output={logs_dir}/{exp_id}_%j.out
#SBATCH --error={logs_dir}/{exp_id}_%j.err

# Experiment: {exp_id}
# Model: {experiment['model']} ({model_config['name']})
# Domain: {experiment['domain']} ({experiment['domain_config']['name']})
# Problem: {experiment['problem']}

echo "Starting experiment: {exp_id}"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "GPUs: {gpus}"

# Load modules
module purge
module load python/3.11.6
module load cuda/12.1

# Navigate to project directory
cd {base_dir}

# Activate virtual environment if available
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Set environment variables
export PYTHONPATH="${{PYTHONPATH}}:{base_dir}/src"
export CUDA_VISIBLE_DEVICES=$(echo $CUDA_VISIBLE_DEVICES | tr ',' ' ' | cut -d' ' -f1-{gpus} | tr ' ' ',')

# Create experiment-specific result directory
RESULT_DIR="{results_dir}/{exp_id}"
mkdir -p "$RESULT_DIR"

# Run the experiment
python3 src/main.py \\
    --model_path "{model_config['path']}" \\
    --domain_file "src/problems/{experiment['domain']}/{experiment['domain_config']['domain_file']}" \\
    --problem_file "src/problems/{experiment['domain']}/{experiment['problem']}" \\
    --output_dir "$RESULT_DIR" \\
    --temperature {model_config['generation_config']['temperature']} \\
    --max_tokens {model_config['generation_config']['max_new_tokens']} \\
    --validate \\
    --save_intermediate \\
    --experiment_id "{exp_id}"

# Check exit status
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "Experiment {exp_id} completed successfully"
    echo "Results saved to: $RESULT_DIR"
else
    echo "Experiment {exp_id} failed with exit code: $EXIT_CODE"
fi

echo "Job completed at: $(date)"
exit $EXIT_CODE
"""
        return script_content
    
    def generate_batch_script(self, experiments: List[Dict[str, Any]], experiment_set: str) -> str:
        """Generate a batch submission script for multiple experiments."""
        
        batch_content = f"""#!/bin/bash
# Batch experiment submission for: {experiment_set}
# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

EXPERIMENT_SET="{experiment_set}"
SCRIPTS_DIR="{self.scripts_dir}"
LOGS_DIR="{self.logs_dir}"

echo "Starting batch submission for experiment set: $EXPERIMENT_SET"
echo "Total experiments: {len(experiments)}"

# Create batch log directory
BATCH_LOG_DIR="$LOGS_DIR/batch_$EXPERIMENT_SET"
mkdir -p "$BATCH_LOG_DIR"

# Job submission with dependency management
declare -a JOB_IDS
MAX_CONCURRENT={self.config['execution']['concurrent_jobs']}
SUBMITTED=0

"""
        
        # Sort experiments by priority
        experiments_sorted = sorted(experiments, key=lambda x: x['priority'])
        
        for i, exp in enumerate(experiments_sorted):
            exp_id = exp['id']
            script_file = f"{exp_id}.sh"
            
            batch_content += f"""
# Submit experiment: {exp_id}
echo "Submitting job {i+1}/{len(experiments)}: {exp_id}"

JOB_OUTPUT=$(sbatch "$SCRIPTS_DIR/{script_file}")
if [ $? -eq 0 ]; then
    JOB_ID=$(echo "$JOB_OUTPUT" | grep -o '[0-9]\\+')
    JOB_IDS+=($JOB_ID)
    echo "  Job ID: $JOB_ID"
    SUBMITTED=$((SUBMITTED + 1))
    
    # Wait if we've hit concurrent limit
    if [ $((SUBMITTED % MAX_CONCURRENT)) -eq 0 ] && [ $SUBMITTED -lt {len(experiments)} ]; then
        echo "  Reached concurrent limit ($MAX_CONCURRENT), waiting for jobs to complete..."
        # Wait for any job to complete before submitting more
        squeue -u $USER --format="%.18i %.9P %.50j %.8u %.8T %.10M %.9l %.6D %R" | grep -E "$(IFS='|'; echo "${{JOB_IDS[*]}}")"
        sleep 30
    fi
else
    echo "  Failed to submit {exp_id}"
fi
"""
        
        batch_content += f"""
echo "Batch submission completed!"
echo "Submitted jobs: $SUBMITTED"
echo "Job IDs: ${{JOB_IDS[@]}}"

# Save job tracking info
echo "${{JOB_IDS[@]}}" > "$BATCH_LOG_DIR/job_ids.txt"
echo "Job IDs saved to: $BATCH_LOG_DIR/job_ids.txt"

# Show queue status
echo "Current queue status:"
squeue -u $USER
"""
        
        return batch_content
    
    def generate_monitoring_script(self, experiment_set: str) -> str:
        """Generate a monitoring script for tracking experiment progress."""
        
        monitor_content = f"""#!/bin/bash
# Experiment monitoring script for: {experiment_set}

EXPERIMENT_SET="{experiment_set}"
LOGS_DIR="{self.logs_dir}"
RESULTS_DIR="{self.results_dir}"
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
echo "Tracking ${{#JOB_IDS[@]}} jobs"

# Show queue status
echo "=== Queue Status ==="
squeue -u $USER --format="%.18i %.9P %.50j %.8u %.8T %.10M %.9l %.6D %R"
echo

# Count job states
RUNNING=0
PENDING=0
COMPLETED=0
FAILED=0

for JOB_ID in "${{JOB_IDS[@]}}"; do
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
echo "Total: ${{#JOB_IDS[@]}}"
echo

# Show recent completions
echo "=== Recent Results ==="
find "$RESULTS_DIR" -name "*{experiment_set}*" -type d -mtime -1 | head -5 | while read result_dir; do
    exp_name=$(basename "$result_dir")
    if [ -f "$result_dir/experiment_results.json" ]; then
        echo "✓ $exp_name - Results available"
    else
        echo "⏳ $exp_name - In progress"
    fi
done

echo
echo "Monitor completed at: $(date)"
"""
        
        return monitor_content
    
    def save_scripts(self, experiments: List[Dict[str, Any]], experiment_set: str):
        """Save all generated scripts to disk."""
        
        print(f"Generating {len(experiments)} experiment scripts...")
        
        # Generate individual experiment scripts
        for exp in experiments:
            script_content = self.generate_slurm_script(exp)
            script_file = self.scripts_dir / f"{exp['id']}.sh"
            
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            # Make executable
            os.chmod(script_file, 0o755)
            
        print(f"✓ Generated {len(experiments)} individual scripts")
        
        # Generate batch submission script
        batch_content = self.generate_batch_script(experiments, experiment_set)
        batch_file = self.scripts_dir / f"submit_{experiment_set}.sh"
        
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        os.chmod(batch_file, 0o755)
        print(f"✓ Generated batch script: {batch_file}")
        
        # Generate monitoring script
        monitor_content = self.generate_monitoring_script(experiment_set)
        monitor_file = self.scripts_dir / f"monitor_{experiment_set}.sh"
        
        with open(monitor_file, 'w') as f:
            f.write(monitor_content)
        os.chmod(monitor_file, 0o755)
        print(f"✓ Generated monitor script: {monitor_file}")
        
        # Save experiment metadata
        metadata = {
            'experiment_set': experiment_set,
            'generated_at': datetime.now().isoformat(),
            'total_experiments': len(experiments),
            'experiments': experiments
        }
        
        metadata_file = self.scripts_dir / f"{experiment_set}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"✓ Saved metadata: {metadata_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate LLM planning experiments")
    parser.add_argument('--config', '-c', required=True,
                       help='Path to experiment configuration file')
    parser.add_argument('--experiment_set', '-e', required=True,
                       help='Name of experiment set to generate')
    parser.add_argument('--base_dir', '-b', 
                       help='Base directory for the project')
    parser.add_argument('--dry_run', action='store_true',
                       help='Show what would be generated without creating files')
    
    args = parser.parse_args()
    
    try:
        # Initialize generator
        generator = ExperimentGenerator(args.config, args.base_dir)
        
        # Generate experiment matrix
        experiments = generator.generate_experiment_matrix(args.experiment_set)
        
        print(f"Experiment Set: {args.experiment_set}")
        print(f"Total Experiments: {len(experiments)}")
        print(f"Models: {set(exp['model'] for exp in experiments)}")
        print(f"Domains: {set(exp['domain'] for exp in experiments)}")
        
        if args.dry_run:
            print("\\n=== DRY RUN - Experiment List ===")
            for exp in experiments:
                print(f"  {exp['id']} - {exp['model']} on {exp['domain']}/{exp['problem']}")
            print("\\nUse --no-dry-run to generate actual scripts")
        else:
            # Generate and save scripts
            generator.save_scripts(experiments, args.experiment_set)
            
            print(f"\\n=== Next Steps ===")
            print(f"1. Review generated scripts in: {generator.scripts_dir}")
            print(f"2. Submit experiments: ./experiments/scripts/submit_{args.experiment_set}.sh")
            print(f"3. Monitor progress: ./experiments/scripts/monitor_{args.experiment_set}.sh")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())