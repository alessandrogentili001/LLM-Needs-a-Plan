#!/usr/bin/env python3
"""
LLM-Needs-a-Plan Experiment Monitor

This script monitors running experiments, collects results, and generates analysis reports.
It provides real-time tracking of experiment progress and automated result aggregation.
"""

import os
import sys
import json
import yaml
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class ExperimentMonitor:
    def __init__(self, base_dir: str = None):
        """Initialize the experiment monitor."""
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        
        self.experiments_dir = self.base_dir / "experiments"
        self.scripts_dir = self.experiments_dir / "scripts"
        self.results_dir = self.experiments_dir / "results"
        self.logs_dir = self.experiments_dir / "logs"
        
        # Load configuration if available
        config_path = self.experiments_dir / "configs" / "experiment_config.yml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}
    
    def get_slurm_jobs(self, user: Optional[str] = None) -> List[Dict[str, str]]:
        """Get current SLURM job status."""
        cmd = ["squeue", "--format=%.18i,%.50j,%.8u,%.8T,%.10M,%.9l,%.6D,%R"]
        if user:
            cmd.extend(["-u", user])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\\n')[1:]  # Skip header
            
            jobs = []
            for line in lines:
                parts = line.split(',')
                if len(parts) >= 8:
                    jobs.append({
                        'job_id': parts[0].strip(),
                        'name': parts[1].strip(),
                        'user': parts[2].strip(), 
                        'state': parts[3].strip(),
                        'time': parts[4].strip(),
                        'time_limit': parts[5].strip(),
                        'nodes': parts[6].strip(),
                        'nodelist': parts[7].strip()
                    })
            return jobs
        except subprocess.CalledProcessError:
            return []
    
    def get_experiment_jobs(self) -> Dict[str, Dict[str, str]]:
        """Get jobs related to our experiments."""
        all_jobs = self.get_slurm_jobs()
        
        experiment_jobs = {}
        for job in all_jobs:
            # Check if job name matches our experiment pattern
            job_name = job['name']
            if any(exp_set in job_name for exp_set in ['quick_test', 'model_comparison', 'domain_analysis', 'comprehensive']):
                experiment_jobs[job['job_id']] = job
        
        return experiment_jobs
    
    def get_completed_jobs(self, since_hours: int = 24) -> List[Dict[str, str]]:
        """Get recently completed jobs using sacct."""
        since_time = datetime.now() - timedelta(hours=since_hours)
        since_str = since_time.strftime('%Y-%m-%dT%H:%M:%S')
        
        cmd = ["sacct", f"--starttime={since_str}", 
               "--format=JobID,JobName,State,ExitCode,Start,End,ElapsedRaw", "--parsable2"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\\n')[1:]  # Skip header
            
            jobs = []
            for line in lines:
                parts = line.split('|')
                if len(parts) >= 7 and not parts[0].endswith('.batch'):  # Skip batch job entries
                    jobs.append({
                        'job_id': parts[0],
                        'name': parts[1],
                        'state': parts[2],
                        'exit_code': parts[3],
                        'start': parts[4],
                        'end': parts[5],
                        'elapsed': parts[6]
                    })
            return jobs
        except subprocess.CalledProcessError:
            return []
    
    def scan_experiment_results(self) -> Dict[str, Dict[str, Any]]:
        """Scan results directory for completed experiments."""
        results = {}
        
        if not self.results_dir.exists():
            return results
        
        for result_dir in self.results_dir.iterdir():
            if result_dir.is_dir():
                exp_id = result_dir.name
                
                # Check for result files
                result_info = {
                    'experiment_id': exp_id,
                    'path': str(result_dir),
                    'files': [],
                    'status': 'incomplete',
                    'created': None,
                    'size_mb': 0
                }
                
                # Scan files in result directory
                total_size = 0
                for file_path in result_dir.glob('*'):
                    if file_path.is_file():
                        file_info = {
                            'name': file_path.name,
                            'size': file_path.stat().st_size,
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                        }
                        result_info['files'].append(file_info)
                        total_size += file_info['size']
                
                result_info['size_mb'] = total_size / (1024 * 1024)
                
                # Determine status based on files
                if any(f['name'] == 'experiment_results.json' for f in result_info['files']):
                    result_info['status'] = 'completed'
                elif result_info['files']:
                    result_info['status'] = 'in_progress'
                
                # Get creation time
                if result_info['files']:
                    result_info['created'] = min(f['modified'] for f in result_info['files'])
                
                results[exp_id] = result_info
        
        return results
    
    def load_experiment_result(self, exp_id: str) -> Optional[Dict[str, Any]]:
        """Load detailed results for a specific experiment."""
        result_dir = self.results_dir / exp_id
        result_file = result_dir / 'experiment_results.json'
        
        if result_file.exists():
            try:
                with open(result_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return None
        return None
    
    def generate_summary_report(self, experiment_set: str = None) -> Dict[str, Any]:
        """Generate a comprehensive summary report."""
        
        # Get job status
        running_jobs = self.get_experiment_jobs()
        completed_jobs = self.get_completed_jobs()
        
        # Get result status
        results = self.scan_experiment_results()
        
        # Filter by experiment set if specified
        if experiment_set:
            results = {k: v for k, v in results.items() if experiment_set in k}
            running_jobs = {k: v for k, v in running_jobs.items() if experiment_set in v['name']}
            completed_jobs = [j for j in completed_jobs if experiment_set in j['name']]
        
        # Calculate statistics
        total_experiments = len(results)
        completed_experiments = len([r for r in results.values() if r['status'] == 'completed'])
        in_progress_experiments = len([r for r in results.values() if r['status'] == 'in_progress'])
        
        # Success rate calculation
        success_rate = (completed_experiments / total_experiments * 100) if total_experiments > 0 else 0
        
        # Resource usage
        total_size_gb = sum(r['size_mb'] for r in results.values()) / 1024
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'experiment_set': experiment_set or 'all',
            'summary': {
                'total_experiments': total_experiments,
                'completed': completed_experiments,
                'in_progress': in_progress_experiments,
                'running_jobs': len(running_jobs),
                'success_rate': round(success_rate, 1),
                'total_size_gb': round(total_size_gb, 2)
            },
            'running_jobs': list(running_jobs.values()),
            'recent_completions': completed_jobs[-10:],  # Last 10
            'results': results
        }
        
        return report
    
    def create_visualizations(self, report: Dict[str, Any], output_dir: Path):
        """Create visualization plots from the report data."""
        
        # Set style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Create output directory
        viz_dir = output_dir / 'visualizations'
        viz_dir.mkdir(exist_ok=True)
        
        # 1. Experiment Status Pie Chart
        fig, ax = plt.subplots(figsize=(8, 6))
        
        status_counts = {
            'Completed': report['summary']['completed'],
            'In Progress': report['summary']['in_progress'],
            'Running': report['summary']['running_jobs']
        }
        
        colors = ['#2ecc71', '#f39c12', '#3498db']
        wedges, texts, autotexts = ax.pie(status_counts.values(), 
                                         labels=status_counts.keys(),
                                         autopct='%1.1f%%',
                                         colors=colors,
                                         startangle=90)
        
        ax.set_title(f'Experiment Status - {report["experiment_set"].title()}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(viz_dir / 'experiment_status.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Success Rate by Model/Domain (if we have detailed results)
        results_with_details = []
        for exp_id, result_info in report['results'].items():
            if result_info['status'] == 'completed':
                details = self.load_experiment_result(exp_id)
                if details:
                    # Parse experiment ID to extract model and domain
                    parts = exp_id.split('_')
                    if len(parts) >= 3:
                        exp_set, model, domain = parts[0], parts[1], parts[2]
                        results_with_details.append({
                            'experiment_set': exp_set,
                            'model': model,
                            'domain': domain,
                            'success': details.get('plan_valid', False),
                            'plan_length': details.get('plan_length', 0),
                            'generation_time': details.get('generation_time_seconds', 0)
                        })
        
        if results_with_details:
            df = pd.DataFrame(results_with_details)
            
            # Success rate by model
            if 'model' in df.columns:
                fig, ax = plt.subplots(figsize=(10, 6))
                success_by_model = df.groupby('model')['success'].agg(['count', 'sum', 'mean']).reset_index()
                success_by_model['success_rate'] = success_by_model['mean'] * 100
                
                bars = ax.bar(success_by_model['model'], success_by_model['success_rate'])
                ax.set_title('Success Rate by Model', fontsize=14, fontweight='bold')
                ax.set_xlabel('Model')
                ax.set_ylabel('Success Rate (%)')
                ax.set_ylim(0, 100)
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                           f'{height:.1f}%', ha='center', va='bottom')
                
                plt.tight_layout()
                plt.savefig(viz_dir / 'success_by_model.png', dpi=300, bbox_inches='tight')
                plt.close()
            
            # Performance metrics
            if len(df) > 1:
                fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
                
                # Plan length distribution
                if df['plan_length'].sum() > 0:
                    df[df['plan_length'] > 0]['plan_length'].hist(bins=20, ax=ax1, alpha=0.7)
                    ax1.set_title('Plan Length Distribution')
                    ax1.set_xlabel('Plan Length')
                    ax1.set_ylabel('Frequency')
                
                # Generation time distribution  
                if df['generation_time'].sum() > 0:
                    df[df['generation_time'] > 0]['generation_time'].hist(bins=20, ax=ax2, alpha=0.7)
                    ax2.set_title('Generation Time Distribution')
                    ax2.set_xlabel('Time (seconds)')
                    ax2.set_ylabel('Frequency')
                
                # Success by domain
                if 'domain' in df.columns:
                    success_by_domain = df.groupby('domain')['success'].mean() * 100
                    success_by_domain.plot(kind='bar', ax=ax3)
                    ax3.set_title('Success Rate by Domain')
                    ax3.set_ylabel('Success Rate (%)')
                    ax3.tick_params(axis='x', rotation=45)
                
                # Model vs Domain heatmap
                if 'model' in df.columns and 'domain' in df.columns:
                    pivot_table = df.pivot_table(values='success', index='model', columns='domain', aggfunc='mean')
                    sns.heatmap(pivot_table * 100, annot=True, fmt='.1f', ax=ax4, cmap='RdYlGn', cbar_kws={'label': 'Success Rate (%)'})
                    ax4.set_title('Success Rate: Model vs Domain')
                
                plt.tight_layout()
                plt.savefig(viz_dir / 'performance_analysis.png', dpi=300, bbox_inches='tight')
                plt.close()
        
        print(f"✓ Visualizations saved to: {viz_dir}")
    
    def save_report(self, report: Dict[str, Any], output_file: Path):
        """Save the report to file."""
        
        # Save JSON report
        json_file = output_file.with_suffix('.json')
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save human-readable summary
        txt_file = output_file.with_suffix('.txt')
        with open(txt_file, 'w') as f:
            f.write(f"LLM-Needs-a-Plan Experiment Report\\n")
            f.write(f"Generated: {report['generated_at']}\\n")
            f.write(f"Experiment Set: {report['experiment_set']}\\n")
            f.write("=" * 50 + "\\n\\n")
            
            # Summary
            summary = report['summary']
            f.write(f"SUMMARY\\n")
            f.write(f"Total Experiments: {summary['total_experiments']}\\n")
            f.write(f"Completed: {summary['completed']}\\n") 
            f.write(f"In Progress: {summary['in_progress']}\\n")
            f.write(f"Running Jobs: {summary['running_jobs']}\\n")
            f.write(f"Success Rate: {summary['success_rate']}%\\n")
            f.write(f"Total Data Size: {summary['total_size_gb']} GB\\n\\n")
            
            # Running jobs
            if report['running_jobs']:
                f.write(f"RUNNING JOBS\\n")
                for job in report['running_jobs']:
                    f.write(f"  {job['job_id']}: {job['name']} ({job['state']})\\n")
                f.write("\\n")
            
            # Recent completions
            if report['recent_completions']:
                f.write(f"RECENT COMPLETIONS\\n")
                for job in report['recent_completions'][-5:]:  # Last 5
                    f.write(f"  {job['name']}: {job['state']} (Exit: {job['exit_code']})\\n")
        
        print(f"✓ Report saved: {json_file} and {txt_file}")


def main():
    parser = argparse.ArgumentParser(description="Monitor LLM planning experiments")
    parser.add_argument('--experiment_set', '-e',
                       help='Monitor specific experiment set')
    parser.add_argument('--output_dir', '-o', 
                       help='Output directory for reports')
    parser.add_argument('--watch', action='store_true',
                       help='Continuous monitoring mode')
    parser.add_argument('--visualize', action='store_true',
                       help='Generate visualization plots')
    
    args = parser.parse_args()
    
    try:
        # Initialize monitor
        monitor = ExperimentMonitor()
        
        # Set output directory
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            output_dir = monitor.experiments_dir / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if args.watch:
            print("Starting continuous monitoring mode (Ctrl+C to stop)...")
            try:
                while True:
                    os.system('clear')  # Clear screen
                    
                    # Generate report
                    report = monitor.generate_summary_report(args.experiment_set)
                    
                    # Display summary
                    print(f"=== LLM-Needs-a-Plan Monitor ===")
                    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"Set: {report['experiment_set']}")
                    print(f"Total: {report['summary']['total_experiments']}")
                    print(f"Completed: {report['summary']['completed']}")
                    print(f"Running: {report['summary']['running_jobs']}")
                    print(f"Success Rate: {report['summary']['success_rate']}%")
                    
                    if report['running_jobs']:
                        print("\\n--- Running Jobs ---")
                        for job in report['running_jobs']:
                            print(f"  {job['job_id']}: {job['name']} ({job['state']})")
                    
                    print("\\n(Refreshing in 30 seconds...)")
                    
                    import time
                    time.sleep(30)
                    
            except KeyboardInterrupt:
                print("\\nMonitoring stopped")
        else:
            # Generate single report
            report = monitor.generate_summary_report(args.experiment_set)
            
            # Save report
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_name = f"experiment_report_{args.experiment_set or 'all'}_{timestamp}"
            monitor.save_report(report, output_dir / report_name)
            
            # Generate visualizations if requested
            if args.visualize:
                monitor.create_visualizations(report, output_dir)
            
            # Display summary
            print(f"\\n=== Experiment Summary ===")
            print(f"Set: {report['experiment_set']}")
            print(f"Total: {report['summary']['total_experiments']}")
            print(f"Completed: {report['summary']['completed']}")
            print(f"Success Rate: {report['summary']['success_rate']}%")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())