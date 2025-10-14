#!/usr/bin/env python3
"""
Temperature Sensitivity Experiment Generator

Focused generator for systematic temperature analysis of Phi4 planning capabilities.
Creates rigorous experimental setup with proper controls and statistical design.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import itertools
import argparse


class TemperatureExperimentGenerator:
    def __init__(self, config_path: str):
        """Initialize the temperature experiment generator."""
        self.config_path = Path(config_path)
        
        # Load experiment configuration
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Set up directories
        self.base_dir = Path(self.config['infrastructure']['paths']['base_dir'])
        self.results_dir = Path(self.config['infrastructure']['paths']['results_dir'])
        self.data_dir = Path(self.config['infrastructure']['paths']['data_dir'])
        
        # Create organized directory structure
        self._setup_experiment_directories()
        
        # Initialize experiment tracking
        self.experiment_conditions = []
        self.experiment_scripts = []
        
    def _setup_experiment_directories(self):
        """Create organized directory structure for temperature experiments."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.exp_root = self.results_dir.parent / f"temperature_analysis_{timestamp}"
        
        self.directories = {
            'root': self.exp_root,
            'configs': self.exp_root / 'configs',
            'scripts': self.exp_root / 'scripts',
            'raw_results': self.exp_root / 'raw_results',
            'processed_data': self.exp_root / 'processed_data',
            'analysis': self.exp_root / 'analysis',
            'visualizations': self.exp_root / 'visualizations',
            'reports': self.exp_root / 'reports'
        }
        
        # Create all directories
        for directory in self.directories.values():
            directory.mkdir(parents=True, exist_ok=True)
            
        print(f"📁 Experiment directory created: {self.exp_root}")
    
    def generate_experimental_conditions(self, phase: str = "full") -> List[Dict[str, Any]]:
        """Generate all experimental conditions based on design."""
        print(f"🔬 Generating {phase} experimental conditions...")
        
        phase_config = self.config['execution'][phase]
        
        # Get temperature values for this phase
        if phase_config['temperature_values'] == 'all':
            temperatures = [t['value'] for t in self.config['model']['temperature_values']]
        else:
            temperatures = phase_config['temperature_subset']
        
        # Get domains for this phase
        if phase_config['domains'] == 'all':
            domains = list(self.config['experimental_design']['domains'].keys())
        else:
            domains = phase_config['domain_subset']
        
        # Get number of runs
        runs_per_condition = phase_config['runs_per_condition']
        
        conditions = []
        condition_id = 1
        
        for temperature in temperatures:
            for domain_name in domains:
                domain_config = self.config['experimental_design']['domains'][domain_name]
                
                for problem in domain_config['problems']:
                    for run in range(runs_per_condition):
                        
                        condition = {
                            'condition_id': condition_id,
                            'temperature': temperature,
                            'domain_name': domain_name,
                            'domain_file': domain_config['domain_file'],
                            'problem_file': problem,
                            'run_number': run + 1,
                            'complexity': domain_config['complexity'],
                            'expected_sensitivity': domain_config['expected_sensitivity'],
                            'phase': phase,
                            'timestamp': datetime.now().isoformat(),
                            
                            # Fixed parameters for this temperature study
                            'fixed_params': self.config['model']['fixed_parameters'],
                            
                            # Experimental metadata
                            'metadata': {
                                'experiment_title': self.config['experiment']['title'],
                                'research_hypothesis': self.config['experiment']['research_hypothesis'],
                                'temperature_description': next(
                                    t['description'] for t in self.config['model']['temperature_values'] 
                                    if t['value'] == temperature
                                ),
                                'expected_behavior': next(
                                    t['expected_behavior'] for t in self.config['model']['temperature_values'] 
                                    if t['value'] == temperature
                                )
                            }
                        }
                        
                        conditions.append(condition)
                        condition_id += 1
        
        self.experiment_conditions = conditions
        
        print(f"  📊 Generated {len(conditions)} experimental conditions")
        print(f"  🌡️  Temperatures: {temperatures}")
        print(f"  🏗️  Domains: {domains}")
        print(f"  🔄 Runs per condition: {runs_per_condition}")
        
        return conditions
    
    def create_slurm_script(self, condition: Dict[str, Any]) -> str:
        """Create SLURM job script for individual experimental condition."""
        condition_id = condition['condition_id']
        temperature = condition['temperature']
        domain_name = condition['domain_name']
        problem = condition['problem_file']
        run_num = condition['run_number']
        
        # Create unique experiment identifier
        exp_id = f"temp_{temperature}_{domain_name}_{problem}_{run_num:02d}"
        
        # Set up result paths
        result_dir = self.directories['raw_results'] / f"temp_{temperature}" / domain_name
        result_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = result_dir / f"{exp_id}_config.json"
        output_file = result_dir / f"{exp_id}_results.json"
        log_dir = self.directories['root'] / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # Infrastructure settings
        infra = self.config['infrastructure']
        
        # Create SLURM script content
        script_content = f"""#!/bin/bash
#SBATCH --job-name={exp_id}
#SBATCH --partition={infra['cluster']['partition']}
#SBATCH --account={infra['cluster']['account']}
#SBATCH --time={infra['cluster']['time_limit']}
#SBATCH --nodes=1
#SBATCH --cpus-per-task={infra['cluster']['cpus']}
#SBATCH --mem={infra['cluster']['memory']}
#SBATCH --gres=gpu:{infra['cluster']['gpus']}
#SBATCH --output={log_dir}/{exp_id}.out
#SBATCH --error={log_dir}/{exp_id}.err

# Temperature Sensitivity Experiment
# Condition ID: {condition_id}
# Temperature: {temperature} - {condition['metadata']['temperature_description']}
# Domain: {domain_name} ({condition['complexity']} complexity)
# Problem: {problem}
# Run: {run_num}

echo "🌡️  Starting Temperature Experiment: {exp_id}"
echo "Temperature: {temperature}"
echo "Expected Behavior: {condition['metadata']['expected_behavior']}"
echo "Timestamp: $(date)"

# Environment setup
export PYTHONPATH={self.base_dir}:$PYTHONPATH
cd {self.base_dir}

# File paths
MODEL_PATH="{self.base_dir}/src/models/Phi4"
DOMAIN_FILE="{self.data_dir}/{condition['domain_file']}"
PROBLEM_FILE="{self.data_dir}/{problem}"
CONFIG_FILE="{config_file}"
OUTPUT_FILE="{output_file}"

# Save experimental condition configuration
cat > "$CONFIG_FILE" << 'EOF'
{json.dumps(condition, indent=2)}
EOF

echo "📋 Configuration saved to: $CONFIG_FILE"

# Build generation command with temperature parameter
PYTHON_CMD="python3 src/main.py"
PYTHON_CMD="$PYTHON_CMD --model \\"$MODEL_PATH\\""
PYTHON_CMD="$PYTHON_CMD --domain \\"$DOMAIN_FILE\\""
PYTHON_CMD="$PYTHON_CMD --problem \\"$PROBLEM_FILE\\""
PYTHON_CMD="$PYTHON_CMD --output \\"$OUTPUT_FILE\\""

# Temperature parameter (primary variable)
PYTHON_CMD="$PYTHON_CMD --temperature {temperature}"

# Fixed parameters (controls)"""

        # Add fixed parameters
        for param_name, param_value in condition['fixed_params'].items():
            script_content += f'\nPYTHON_CMD="$PYTHON_CMD --{param_name} {param_value}"'
        
        script_content += f"""

# Experimental tracking parameters
PYTHON_CMD="$PYTHON_CMD --experiment-id \\"{exp_id}\\""
PYTHON_CMD="$PYTHON_CMD --temperature-study true"
PYTHON_CMD="$PYTHON_CMD --condition-id {condition_id}"

# Validation and analysis flags
PYTHON_CMD="$PYTHON_CMD --validate true"
PYTHON_CMD="$PYTHON_CMD --detailed-analysis true"
PYTHON_CMD="$PYTHON_CMD --save-reasoning true"

echo "🚀 Executing: $PYTHON_CMD"

# Record start time
START_TIME=$(date +%s)

# Execute the experiment
eval $PYTHON_CMD
EXIT_CODE=$?

# Record end time
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Process results
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Experiment completed successfully in ${{DURATION}}s"
    
    # Add execution metadata to results
    if [ -f "$OUTPUT_FILE" ]; then
        python3 -c "
import json
from datetime import datetime

# Load existing results
with open('$OUTPUT_FILE', 'r') as f:
    results = json.load(f)

# Add execution metadata
results['execution_metadata'] = {{
    'exit_code': $EXIT_CODE,
    'duration_seconds': $DURATION,
    'completion_time': datetime.now().isoformat(),
    'experiment_phase': '{condition['phase']}',
    'temperature_condition': {temperature},
    'slurm_job_id': os.environ.get('SLURM_JOB_ID', 'unknown')
}}

# Save updated results
with open('$OUTPUT_FILE', 'w') as f:
    json.dump(results, f, indent=2)
" 
        echo "📊 Results metadata updated"
    fi
    
else
    echo "❌ Experiment failed with exit code $EXIT_CODE after ${{DURATION}}s"
    
    # Create failure record
    python3 -c "
import json
from datetime import datetime

failure_record = {{
    'status': 'failed',
    'exit_code': $EXIT_CODE,
    'duration_seconds': $DURATION,
    'failure_time': datetime.now().isoformat(),
    'condition': {json.dumps(condition)},
    'requires_investigation': True
}}

with open('$OUTPUT_FILE', 'w') as f:
    json.dump(failure_record, f, indent=2)
"
    echo "📝 Failure record created"
fi

echo "🏁 Temperature experiment {exp_id} finished at: $(date)"
"""
        
        return script_content
    
    def generate_experiment_batch(self, phase: str = "full") -> Dict[str, Any]:
        """Generate complete experimental batch with all scripts and metadata."""
        print(f"🚀 Generating {phase} temperature experiment batch...")
        
        # Generate experimental conditions
        conditions = self.generate_experimental_conditions(phase)
        
        # Create SLURM scripts for each condition
        scripts = []
        for condition in conditions:
            script_content = self.create_slurm_script(condition)
            
            exp_id = f"temp_{condition['temperature']}_{condition['domain_name']}_{condition['problem_file']}_{condition['run_number']:02d}"
            script_file = self.directories['scripts'] / f"{exp_id}.sh"
            
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            # Make executable
            os.chmod(script_file, 0o755)
            scripts.append(str(script_file))
        
        # Save experimental design metadata
        experiment_metadata = {
            'experiment_info': self.config['experiment'],
            'generation_timestamp': datetime.now().isoformat(),
            'phase': phase,
            'total_conditions': len(conditions),
            'temperature_values': list(set(c['temperature'] for c in conditions)),
            'domains_tested': list(set(c['domain_name'] for c in conditions)),
            'runs_per_condition': self.config['execution'][phase]['runs_per_condition'],
            'expected_duration': f"{len(conditions) * 30} minutes (estimated)",
            'directories': {k: str(v) for k, v in self.directories.items()},
            'conditions': conditions
        }
        
        metadata_file = self.directories['root'] / f'{phase}_experiment_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(experiment_metadata, f, indent=2)
        
        # Create experiment summary
        temp_values = sorted(list(set(c['temperature'] for c in conditions)))
        domains = list(set(c['domain_name'] for c in conditions))
        runs_per_condition = self.config['execution'][phase]['runs_per_condition']
        
        summary = {
            'experiment_batch': f"{phase}_temperature_analysis",
            'total_scripts': len(scripts),
            'script_directory': str(self.directories['scripts']),
            'results_directory': str(self.directories['raw_results']),
            'metadata_file': str(metadata_file),
            'scripts': scripts,
            'temperature_range': f"{min(temp_values)}-{max(temp_values)}" if len(temp_values) > 1 else str(temp_values[0]),
            'domains': ", ".join(domains),
            'runs_per_condition': runs_per_condition
        }
        
        return summary
    
    def create_submission_helper(self, batch_summary: Dict[str, Any]) -> str:
        """Create helper script for batch job submission."""
        submission_script = self.directories['root'] / 'submit_experiments.sh'
        
        script_content = f"""#!/bin/bash
# Temperature Sensitivity Experiment Batch Submission
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SCRIPT_DIR="{batch_summary['script_directory']}"
TOTAL_SCRIPTS={batch_summary['total_scripts']}

echo "🌡️  Temperature Sensitivity Experiment Batch Submission"
echo "=================================================="
echo "Total experiments: $TOTAL_SCRIPTS"
echo "Script directory: $SCRIPT_DIR"
echo ""

# Function to submit experiments with temperature grouping
submit_by_temperature() {{
    echo "🚀 Submitting experiments grouped by temperature..."
    
    for temp_script in "$SCRIPT_DIR"/temp_*.sh; do
        if [ -f "$temp_script" ]; then
            echo "Submitting: $(basename "$temp_script")"
            sbatch "$temp_script"
            sleep 2  # Small delay to avoid overwhelming scheduler
        fi
    done
}}

# Function to submit pilot experiments only
submit_pilot() {{
    echo "🧪 Submitting pilot experiments (temperatures: 0.0, 0.3, 0.7)..."
    
    for temp in 0.0 0.3 0.7; do
        for script in "$SCRIPT_DIR"/temp_${{temp}}_*.sh; do
            if [ -f "$script" ]; then
                echo "Submitting pilot: $(basename "$script")"
                sbatch "$script"
                sleep 2
            fi
        done
    done
}}

# Function to check experiment status
check_status() {{
    echo "📊 Checking experiment status..."
    squeue -u $USER --format="%.18i %.50j %.8u %.8T %.10M %.9l"
}}

# Main menu
echo "Choose submission strategy:"
echo "1. Submit all experiments"
echo "2. Submit pilot experiments only"
echo "3. Check job status"
echo "4. Show experiment summary"

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        submit_by_temperature
        ;;
    2)
        submit_pilot
        ;;
    3)
        check_status
        ;;
    4)
        echo ""
        echo "📋 Experiment Summary:"
        echo "  Total conditions: $TOTAL_SCRIPTS"
        echo "  Temperature values: {batch_summary['temperature_range']}"
        echo "  Domains: {batch_summary['domains']}"
        echo "  Runs per condition: {batch_summary['runs_per_condition']}"
        echo "  Expected total time: ~{batch_summary['total_scripts'] * 30} minutes"
        echo ""
        echo "📁 Key directories:"
        echo "  Scripts: $SCRIPT_DIR"
        echo "  Results: {self.directories['raw_results']}"
        echo "  Analysis: {self.directories['analysis']}"
        ;;
    *)
        echo "Invalid choice"
        ;;
esac
"""
        
        with open(submission_script, 'w') as f:
            f.write(script_content)
        
        os.chmod(submission_script, 0o755)
        
        print(f"📝 Submission helper created: {submission_script}")
        return str(submission_script)


def main():
    """Main entry point for temperature experiment generation."""
    parser = argparse.ArgumentParser(description="Temperature Sensitivity Experiment Generator")
    parser.add_argument("--config", type=str, 
                       default="experiments/configs/temperature_experiment.yml",
                       help="Temperature experiment configuration file")
    parser.add_argument("--phase", choices=['pilot', 'full'], default='full',
                       help="Experimental phase to generate")
    parser.add_argument("--dry-run", action='store_true',
                       help="Show what would be generated without creating files")
    
    args = parser.parse_args()
    
    try:
        print("🌡️  Temperature Sensitivity Experiment Generator")
        print("=" * 60)
        
        generator = TemperatureExperimentGenerator(args.config)
        
        if args.dry_run:
            print("📋 DRY RUN - Previewing experiment generation")
            conditions = generator.generate_experimental_conditions(args.phase)
            
            print(f"\n📊 Would generate {len(conditions)} experimental conditions:")
            
            # Group by temperature for summary
            by_temp = {}
            for condition in conditions:
                temp = condition['temperature']
                if temp not in by_temp:
                    by_temp[temp] = 0
                by_temp[temp] += 1
            
            for temp in sorted(by_temp.keys()):
                print(f"  🌡️  Temperature {temp}: {by_temp[temp]} conditions")
            
            print(f"\n📁 Would create directory structure at:")
            print(f"  {generator.directories['root']}")
            
        else:
            # Generate actual experiments
            batch_summary = generator.generate_experiment_batch(args.phase)
            
            # Create submission helper
            submission_script = generator.create_submission_helper(batch_summary)
            
            # Print summary
            print("\n" + "=" * 60)
            print("🎉 Temperature Experiment Generation Complete!")
            
            print(f"\n📊 Batch Summary:")
            print(f"  Phase: {args.phase}")
            print(f"  Total experiments: {batch_summary['total_scripts']}")
            print(f"  Script directory: {batch_summary['script_directory']}")
            
            print(f"\n🚀 Next Steps:")
            print(f"  1. Review experiment setup: {generator.directories['root']}")
            print(f"  2. Submit experiments: {submission_script}")
            print(f"  3. Monitor progress with SLURM commands")
            print(f"  4. Analyze results when complete")
            
            print(f"\n📁 Key Files Created:")
            print(f"  • Experiment metadata: {generator.directories['root']}/{args.phase}_experiment_metadata.json")
            print(f"  • Submission helper: {submission_script}")
            print(f"  • SLURM scripts: {batch_summary['total_scripts']} files in {batch_summary['script_directory']}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()