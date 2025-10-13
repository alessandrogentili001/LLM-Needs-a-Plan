#!/usr/bin/env python3
"""
Simple Experiment Monitor (No Visualization Dependencies)

This is a simplified version of the experiment monitor that doesn't require
matplotlib or seaborn, making it suitable for cluster environments.
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


class SimpleExperimentMonitor:
    def __init__(self, base_dir: str = None):
        """Initialize the experiment monitor."""
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        
        # Fix nested path issue
        if "experiments" in str(self.base_dir).split('/')[-1]:
            # If base_dir is already experiments directory
            self.experiments_dir = self.base_dir
            self.scripts_dir = self.base_dir / "scripts"
            self.results_dir = self.base_dir / "results"
            self.logs_dir = self.base_dir / "logs"
            config_path = self.base_dir / "configs" / "experiment_config.yml"
        else:
            # If base_dir is project root
            self.experiments_dir = self.base_dir / "experiments"
            self.scripts_dir = self.experiments_dir / "scripts"
            self.results_dir = self.experiments_dir / "results"
            self.logs_dir = self.experiments_dir / "logs"
            config_path = self.experiments_dir / "configs" / "experiment_config.yml"
        
        # Load configuration if available
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}
    
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
    
    def generate_summary_report(self, experiment_set: str = None) -> Dict[str, Any]:
        """Generate a comprehensive summary report."""
        
        # Get result status
        results = self.scan_experiment_results()
        
        # Filter by experiment set if specified
        if experiment_set:
            results = {k: v for k, v in results.items() if experiment_set in k}
        
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
                'success_rate': round(success_rate, 1),
                'total_size_gb': round(total_size_gb, 2)
            },
            'results': results
        }
        
        return report
    
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
    
    def display_summary(self, report: Dict[str, Any]):
        """Display a formatted summary report."""
        
        print(f"=== LLM-Needs-a-Plan Experiment Summary ===")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Experiment Set: {report['experiment_set']}")
        print(f"=" * 50)
        
        # Summary statistics
        summary = report['summary']
        print(f"\\nSUMMARY:")
        print(f"  Total Experiments: {summary['total_experiments']}")
        print(f"  Completed: {summary['completed']}")
        print(f"  In Progress: {summary['in_progress']}")
        print(f"  Success Rate: {summary['success_rate']}%")
        print(f"  Total Data Size: {summary['total_size_gb']} GB")
        
        # Individual experiment status
        if report['results']:
            print(f"\\nEXPERIMENT STATUS:")
            for exp_id, result in report['results'].items():
                status_symbol = {
                    'completed': '✓',
                    'in_progress': '⏳',
                    'incomplete': '⭕'
                }.get(result['status'], '?')
                
                print(f"  {status_symbol} {exp_id}: {result['status'].replace('_', ' ').title()}")
                
                if result['status'] == 'completed':
                    # Try to load detailed results
                    detailed = self.load_experiment_result(exp_id)
                    if detailed:
                        validity = "✓" if detailed.get('plan_valid', False) else "✗"
                        plan_length = detailed.get('plan_length', 0)
                        gen_time = detailed.get('generation_time_seconds', 0)
                        print(f"    Plan Valid: {validity}, Length: {plan_length}, Time: {gen_time:.1f}s")
        
        print(f"\\n" + "=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Simple experiment monitor")
    parser.add_argument('--experiment_set', '-e',
                       help='Monitor specific experiment set')
    parser.add_argument('--base_dir', '-b',
                       help='Base directory for the project')
    
    args = parser.parse_args()
    
    try:
        # Initialize monitor
        base_dir = args.base_dir or os.getcwd()
        monitor = SimpleExperimentMonitor(base_dir)
        
        # Generate and display report
        report = monitor.generate_summary_report(args.experiment_set)
        monitor.display_summary(report)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())