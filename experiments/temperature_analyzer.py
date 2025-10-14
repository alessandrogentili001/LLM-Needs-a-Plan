#!/usr/bin/env python3
"""
Temperature Analysis Tool

Specialized analysis for temperature sensitivity experiments.
Provides statistical rigor and clear insights into temperature effects on planning.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from scipy import stats
from scipy.optimize import curve_fit
import argparse


class TemperatureAnalyzer:
    def __init__(self, experiment_dir: str):
        """Initialize temperature analysis for specific experiment directory."""
        self.experiment_dir = Path(experiment_dir)
        
        # Set up analysis directories
        self.raw_results_dir = self.experiment_dir / 'raw_results'
        self.analysis_dir = self.experiment_dir / 'analysis'
        self.viz_dir = self.experiment_dir / 'visualizations'
        self.reports_dir = self.experiment_dir / 'reports'
        
        for directory in [self.analysis_dir, self.viz_dir, self.reports_dir]:
            directory.mkdir(exist_ok=True)
        
        # Load experiment metadata
        self._load_experiment_metadata()
        
        # Initialize data structures
        self.results_df = pd.DataFrame()
        self.temperature_analysis = {}
        
        # Set plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def _load_experiment_metadata(self):
        """Load experiment metadata and configuration."""
        metadata_files = list(self.experiment_dir.glob('*_experiment_metadata.json'))
        
        if metadata_files:
            with open(metadata_files[0], 'r') as f:
                self.metadata = json.load(f)
            print(f"📋 Loaded experiment metadata: {metadata_files[0].name}")
        else:
            self.metadata = {}
            print("⚠️  No experiment metadata found")
    
    def load_temperature_results(self) -> pd.DataFrame:
        """Load and process all temperature experiment results."""
        print("🔍 Loading temperature experiment results...")
        
        results = []
        
        # Find all result files in temperature subdirectories
        for temp_dir in self.raw_results_dir.glob('temp_*'):
            if not temp_dir.is_dir():
                continue
                
            temperature = float(temp_dir.name.replace('temp_', ''))
            
            # Load all results for this temperature
            for result_file in temp_dir.rglob('*_results.json'):
                try:
                    with open(result_file, 'r') as f:
                        result_data = json.load(f)
                    
                    # Load corresponding config
                    config_file = result_file.parent / result_file.name.replace('_results.json', '_config.json')
                    if config_file.exists():
                        with open(config_file, 'r') as f:
                            config_data = json.load(f)
                    else:
                        config_data = {}
                    
                    # Process into standardized format
                    processed_result = self._process_single_result(result_data, config_data, temperature)
                    if processed_result:
                        results.append(processed_result)
                        
                except Exception as e:
                    print(f"  ⚠️  Failed to load {result_file}: {e}")
        
        if results:
            self.results_df = pd.DataFrame(results)
            print(f"✅ Loaded {len(results)} temperature experiment results")
            
            # Display basic statistics
            print(f"  🌡️  Temperature range: {self.results_df['temperature'].min()} - {self.results_df['temperature'].max()}")
            print(f"  🏗️  Domains: {', '.join(self.results_df['domain'].unique())}")
            print(f"  📊 Success rate: {self.results_df['goal_achieved'].mean():.2%}")
        else:
            print("❌ No valid results found")
        
        return self.results_df
    
    def _process_single_result(self, result_data: Dict[str, Any], 
                              config_data: Dict[str, Any], temperature: float) -> Optional[Dict[str, Any]]:
        """Process individual result into standardized format."""
        
        # Skip failed experiments
        if result_data.get('status') == 'failed':
            return None
        
        try:
            processed = {
                # Experimental conditions
                'temperature': temperature,
                'domain': config_data.get('domain_name', 'unknown'),
                'problem': config_data.get('problem_file', 'unknown'),
                'run_number': config_data.get('run_number', 1),
                'complexity': config_data.get('complexity', 'unknown'),
                
                # Planning metrics
                'plan_generated': 'plan' in result_data,
                'plan_valid': result_data.get('plan_valid', False),
                'plan_executable': result_data.get('plan_executable', False),
                'goal_achieved': result_data.get('goal_achieved', False),
                'plan_length': len(result_data.get('plan', [])),
                
                # Performance metrics
                'generation_time': result_data.get('generation_time', 0),
                'validation_time': result_data.get('validation_time', 0),
                'total_time': result_data.get('total_time', 0),
                'tokens_generated': result_data.get('tokens_generated', 0),
                
                # Quality metrics
                'plan_optimality': result_data.get('plan_optimality', 0),
                'action_diversity': len(set([action.split('(')[0] for action in result_data.get('plan', [])])) / max(len(result_data.get('plan', [])), 1),
                
                # Execution metadata
                'duration_seconds': result_data.get('execution_metadata', {}).get('duration_seconds', 0),
                'completion_status': result_data.get('execution_metadata', {}).get('exit_code', -1) == 0
            }
            
            return processed
            
        except Exception as e:
            print(f"  ⚠️  Error processing result: {e}")
            return None
    
    def analyze_temperature_effects(self) -> Dict[str, Any]:
        """Comprehensive analysis of temperature effects on planning performance."""
        print("🔬 Analyzing temperature effects...")
        
        if self.results_df.empty:
            return {}
        
        analysis = {}
        
        # 1. Overall temperature performance
        temp_performance = self.results_df.groupby('temperature').agg({
            'goal_achieved': ['mean', 'std', 'count'],
            'plan_valid': 'mean',
            'plan_executable': 'mean',
            'generation_time': ['mean', 'std'],
            'plan_length': ['mean', 'std'],
            'action_diversity': ['mean', 'std']
        }).round(4)
        
        analysis['temperature_performance'] = temp_performance.to_dict()
        
        # 2. Statistical significance testing
        temperatures = sorted(self.results_df['temperature'].unique())
        
        # ANOVA for goal achievement across temperatures
        temp_groups = [self.results_df[self.results_df['temperature'] == t]['goal_achieved'] 
                      for t in temperatures]
        
        if len(temp_groups) > 2 and all(len(group) > 0 for group in temp_groups):
            f_stat, p_value = stats.f_oneway(*temp_groups)
            analysis['anova_goal_achievement'] = {
                'f_statistic': float(f_stat),
                'p_value': float(p_value),
                'significant': p_value < 0.05,
                'interpretation': 'Significant temperature effect' if p_value < 0.05 else 'No significant temperature effect'
            }
        
        # 3. Correlation analysis
        correlations = {}
        metrics = ['goal_achieved', 'plan_valid', 'generation_time', 'plan_length', 'action_diversity']
        
        for metric in metrics:
            if metric in self.results_df.columns:
                corr, p_val = stats.pearsonr(self.results_df['temperature'], self.results_df[metric])
                correlations[metric] = {
                    'correlation': float(corr),
                    'p_value': float(p_val),
                    'significant': p_val < 0.05,
                    'direction': 'positive' if corr > 0 else 'negative'
                }
        
        analysis['temperature_correlations'] = correlations
        
        # 4. Domain-specific analysis
        domain_analysis = {}
        for domain in self.results_df['domain'].unique():
            domain_data = self.results_df[self.results_df['domain'] == domain]
            
            domain_temp_perf = domain_data.groupby('temperature')['goal_achieved'].agg(['mean', 'count'])
            
            # Find optimal temperature for this domain
            optimal_temp = domain_temp_perf['mean'].idxmax()
            optimal_success_rate = domain_temp_perf['mean'].max()
            
            domain_analysis[domain] = {
                'optimal_temperature': float(optimal_temp),
                'optimal_success_rate': float(optimal_success_rate),
                'temperature_performance': domain_temp_perf.to_dict(),
                'sample_sizes': domain_temp_perf['count'].to_dict()
            }
        
        analysis['domain_specific'] = domain_analysis
        
        # 5. Consistency analysis
        consistency_analysis = {}
        for temp in temperatures:
            temp_data = self.results_df[self.results_df['temperature'] == temp]
            
            # Group by problem to analyze consistency
            problem_consistency = temp_data.groupby(['domain', 'problem'])['goal_achieved'].agg(['mean', 'std']).reset_index()
            
            avg_consistency = 1 - problem_consistency['std'].mean()  # 1 - average std deviation
            
            consistency_analysis[temp] = {
                'consistency_score': float(avg_consistency),
                'problem_variations': problem_consistency[['domain', 'problem', 'mean', 'std']].to_dict('records')
            }
        
        analysis['consistency'] = consistency_analysis
        
        # 6. Optimal temperature identification
        overall_performance = self.results_df.groupby('temperature')['goal_achieved'].mean()
        optimal_temp = overall_performance.idxmax()
        
        analysis['optimal_temperature'] = {
            'value': float(optimal_temp),
            'success_rate': float(overall_performance.max()),
            'confidence_interval': self._calculate_confidence_interval(
                self.results_df[self.results_df['temperature'] == optimal_temp]['goal_achieved']
            )
        }
        
        self.temperature_analysis = analysis
        return analysis
    
    def _calculate_confidence_interval(self, data: pd.Series, confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for success rate."""
        n = len(data)
        mean = data.mean()
        se = stats.sem(data)  # Standard error
        h = se * stats.t.ppf((1 + confidence) / 2, n - 1)  # t-distribution
        
        return (float(mean - h), float(mean + h))
    
    def create_temperature_visualizations(self) -> Dict[str, str]:
        """Create comprehensive visualizations of temperature effects."""
        print("🎨 Creating temperature visualizations...")
        
        if self.results_df.empty:
            return {}
        
        viz_files = {}
        
        # 1. Main temperature performance plot
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Temperature Effects on Phi4 Planning Performance', fontsize=16, fontweight='bold')
        
        # Success rate by temperature
        temp_success = self.results_df.groupby('temperature')['goal_achieved'].agg(['mean', 'sem']).reset_index()
        axes[0, 0].errorbar(temp_success['temperature'], temp_success['mean'], 
                           yerr=temp_success['sem'], marker='o', linewidth=2, markersize=8)
        axes[0, 0].set_xlabel('Temperature')
        axes[0, 0].set_ylabel('Success Rate')
        axes[0, 0].set_title('Goal Achievement by Temperature')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_ylim(0, 1)
        
        # Generation time by temperature
        temp_time = self.results_df.groupby('temperature')['generation_time'].agg(['mean', 'sem']).reset_index()
        axes[0, 1].errorbar(temp_time['temperature'], temp_time['mean'], 
                           yerr=temp_time['sem'], marker='s', linewidth=2, markersize=8, color='orange')
        axes[0, 1].set_xlabel('Temperature')
        axes[0, 1].set_ylabel('Generation Time (s)')
        axes[0, 1].set_title('Generation Time by Temperature')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plan length distribution
        temps_to_plot = sorted(self.results_df['temperature'].unique())[::2]  # Every other temperature
        for temp in temps_to_plot:
            temp_data = self.results_df[self.results_df['temperature'] == temp]
            axes[1, 0].hist(temp_data['plan_length'], alpha=0.6, label=f'T={temp}', bins=15)
        axes[1, 0].set_xlabel('Plan Length')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].set_title('Plan Length Distribution by Temperature')
        axes[1, 0].legend()
        
        # Action diversity vs temperature
        temp_diversity = self.results_df.groupby('temperature')['action_diversity'].agg(['mean', 'sem']).reset_index()
        axes[1, 1].errorbar(temp_diversity['temperature'], temp_diversity['mean'], 
                           yerr=temp_diversity['sem'], marker='^', linewidth=2, markersize=8, color='green')
        axes[1, 1].set_xlabel('Temperature')
        axes[1, 1].set_ylabel('Action Diversity')
        axes[1, 1].set_title('Action Diversity by Temperature')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        main_viz_file = self.viz_dir / 'temperature_performance_analysis.png'
        plt.savefig(main_viz_file, dpi=300, bbox_inches='tight')
        plt.close()
        viz_files['main_analysis'] = str(main_viz_file)
        
        # 2. Domain-specific temperature effects
        if len(self.results_df['domain'].unique()) > 1:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Create heatmap of success rates
            heatmap_data = self.results_df.pivot_table(
                index='domain', columns='temperature', values='goal_achieved', aggfunc='mean'
            )
            
            sns.heatmap(heatmap_data, annot=True, cmap='RdYlGn', ax=ax, 
                       fmt='.2f', cbar_kws={'label': 'Success Rate'})
            ax.set_title('Temperature Effects by Domain')
            ax.set_xlabel('Temperature')
            ax.set_ylabel('Domain')
            
            domain_viz_file = self.viz_dir / 'temperature_domain_heatmap.png'
            plt.savefig(domain_viz_file, dpi=300, bbox_inches='tight')
            plt.close()
            viz_files['domain_heatmap'] = str(domain_viz_file)
        
        # 3. Statistical significance visualization
        if 'temperature_correlations' in self.temperature_analysis:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            correlations = self.temperature_analysis['temperature_correlations']
            metrics = list(correlations.keys())
            corr_values = [correlations[m]['correlation'] for m in metrics]
            significance = [correlations[m]['significant'] for m in metrics]
            
            colors = ['red' if sig else 'lightcoral' for sig in significance]
            bars = ax.barh(metrics, corr_values, color=colors)
            
            ax.set_xlabel('Correlation with Temperature')
            ax.set_title('Temperature Correlation Analysis\n(Red = Significant, Light Red = Not Significant)')
            ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
            ax.grid(True, alpha=0.3)
            
            # Add correlation values as text
            for i, (bar, val) in enumerate(zip(bars, corr_values)):
                ax.text(val + 0.01 if val >= 0 else val - 0.01, i, f'{val:.3f}', 
                       va='center', ha='left' if val >= 0 else 'right')
            
            correlation_viz_file = self.viz_dir / 'temperature_correlations.png'
            plt.savefig(correlation_viz_file, dpi=300, bbox_inches='tight')
            plt.close()
            viz_files['correlations'] = str(correlation_viz_file)
        
        return viz_files
    
    def generate_temperature_report(self) -> str:
        """Generate comprehensive temperature analysis report."""
        print("📋 Generating temperature analysis report...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f'temperature_analysis_report_{timestamp}.html'
        
        # Ensure analysis is complete
        if not self.temperature_analysis:
            self.analyze_temperature_effects()
        
        # Create visualizations
        viz_files = self.create_temperature_visualizations()
        
        # Generate HTML report
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Temperature Sensitivity Analysis - Phi4 Planning</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 100%); 
                   color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .section {{ margin: 30px 0; padding: 20px; border: 1px solid #e1e5e9; border-radius: 8px; }}
        .finding {{ background-color: #e8f5e8; padding: 15px; margin: 10px 0; border-left: 4px solid #28a745; }}
        .warning {{ background-color: #fff3cd; padding: 15px; margin: 10px 0; border-left: 4px solid #ffc107; }}
        .metric {{ background-color: #f8f9fa; padding: 10px; margin: 5px; border-radius: 5px; display: inline-block; }}
        .significant {{ color: #dc3545; font-weight: bold; }}
        .visualization {{ text-align: center; margin: 20px 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #dee2e6; padding: 12px; text-align: left; }}
        th {{ background-color: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌡️ Temperature Sensitivity Analysis</h1>
        <h2>Phi4 Planning Performance Study</h2>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Experiments:</strong> {len(self.results_df)}</p>
        <p><strong>Temperature Range:</strong> {self.results_df['temperature'].min()} - {self.results_df['temperature'].max()}</p>
    </div>
"""
        
        # Executive Summary
        if self.temperature_analysis:
            optimal_temp = self.temperature_analysis['optimal_temperature']
            overall_success = self.results_df['goal_achieved'].mean()
            
            html_content += f"""
    <div class="section">
        <h2>📊 Executive Summary</h2>
        
        <div class="finding">
            <strong>🎯 Optimal Temperature Identified:</strong> {optimal_temp['value']} 
            (Success Rate: {optimal_temp['success_rate']:.1%})
        </div>
        
        <div class="metric">Overall Success Rate: {overall_success:.1%}</div>
        <div class="metric">Temperatures Tested: {len(self.results_df['temperature'].unique())}</div>
        <div class="metric">Domains Analyzed: {len(self.results_df['domain'].unique())}</div>
        <div class="metric">Total Conditions: {len(self.results_df)}</div>
        
        <h3>Key Findings:</h3>
        <ul>
"""
            
            # Add key findings based on analysis
            if 'anova_goal_achievement' in self.temperature_analysis:
                anova_result = self.temperature_analysis['anova_goal_achievement']
                if anova_result['significant']:
                    html_content += f"""            <li class="significant">Statistically significant temperature effect detected (p = {anova_result['p_value']:.4f})</li>\n"""
                else:
                    html_content += f"""            <li>No statistically significant temperature effect (p = {anova_result['p_value']:.4f})</li>\n"""
            
            # Add correlation insights
            if 'temperature_correlations' in self.temperature_analysis:
                correlations = self.temperature_analysis['temperature_correlations']
                
                significant_corrs = [(metric, data) for metric, data in correlations.items() if data['significant']]
                
                if significant_corrs:
                    html_content += f"""            <li>Significant correlations found: """
                    for metric, data in significant_corrs[:3]:  # Show top 3
                        direction = "↑" if data['direction'] == 'positive' else "↓"
                        html_content += f"{metric} {direction} (r={data['correlation']:.3f}), "
                    html_content = html_content.rstrip(', ') + "</li>\n"
            
            html_content += """        </ul>
    </div>
"""
        
        # Temperature Performance Analysis
        if 'temperature_performance' in self.temperature_analysis:
            html_content += """
    <div class="section">
        <h2>🔬 Temperature Performance Analysis</h2>
        
        <table>
            <tr>
                <th>Temperature</th>
                <th>Success Rate</th>
                <th>Std Dev</th>
                <th>Experiments</th>
                <th>Avg Generation Time</th>
                <th>Plan Validity</th>
            </tr>
"""
            
            temp_perf = self.temperature_analysis['temperature_performance']
            
            for temp in sorted([float(t) for t in temp_perf['goal_achieved']['mean'].keys()]):
                temp_str = str(temp)
                success_rate = temp_perf['goal_achieved']['mean'][temp_str]
                std_dev = temp_perf['goal_achieved']['std'][temp_str]
                count = temp_perf['goal_achieved']['count'][temp_str]
                gen_time = temp_perf['generation_time']['mean'][temp_str]
                plan_valid = temp_perf['plan_valid']['mean'][temp_str]
                
                # Highlight optimal temperature
                row_class = ' style="background-color: #d4edda;"' if temp == optimal_temp['value'] else ''
                
                html_content += f"""            <tr{row_class}>
                <td>{temp}</td>
                <td>{success_rate:.1%}</td>
                <td>{std_dev:.3f}</td>
                <td>{count}</td>
                <td>{gen_time:.2f}s</td>
                <td>{plan_valid:.1%}</td>
            </tr>\n"""
            
            html_content += """        </table>
    </div>
"""
        
        # Domain-Specific Analysis
        if 'domain_specific' in self.temperature_analysis:
            html_content += """
    <div class="section">
        <h2>🏗️ Domain-Specific Temperature Effects</h2>
"""
            
            domain_analysis = self.temperature_analysis['domain_specific']
            
            for domain, analysis in domain_analysis.items():
                optimal_domain_temp = analysis['optimal_temperature']
                optimal_domain_success = analysis['optimal_success_rate']
                
                html_content += f"""
        <h3>{domain.title()} Domain</h3>
        <div class="finding">
            <strong>Optimal Temperature:</strong> {optimal_domain_temp} 
            (Success Rate: {optimal_domain_success:.1%})
        </div>
"""
            
            html_content += "    </div>\n"
        
        # Visualizations
        if viz_files:
            html_content += """
    <div class="section">
        <h2>📈 Analysis Visualizations</h2>
"""
            
            for viz_name, viz_path in viz_files.items():
                viz_filename = Path(viz_path).name
                title = viz_name.replace('_', ' ').title()
                
                html_content += f"""        <div class="visualization">
            <h3>{title}</h3>
            <img src="../visualizations/{viz_filename}" alt="{viz_name}" style="max-width: 100%; height: auto;">
        </div>
"""
            
            html_content += "    </div>\n"
        
        # Statistical Analysis
        if 'temperature_correlations' in self.temperature_analysis:
            html_content += """
    <div class="section">
        <h2>📊 Statistical Analysis</h2>
        
        <h3>Temperature Correlation Analysis</h3>
        <table>
            <tr><th>Metric</th><th>Correlation</th><th>P-Value</th><th>Significance</th><th>Direction</th></tr>
"""
            
            correlations = self.temperature_analysis['temperature_correlations']
            
            for metric, data in correlations.items():
                significance = "Yes" if data['significant'] else "No"
                sig_class = ' class="significant"' if data['significant'] else ''
                
                html_content += f"""            <tr>
                <td>{metric.replace('_', ' ').title()}</td>
                <td>{data['correlation']:.4f}</td>
                <td>{data['p_value']:.4f}</td>
                <td{sig_class}>{significance}</td>
                <td>{data['direction'].title()}</td>
            </tr>\n"""
            
            html_content += "        </table>\n    </div>\n"
        
        # Recommendations
        html_content += """
    <div class="section">
        <h2>💡 Recommendations</h2>
        
        <div class="finding">
            <h3>🎯 Temperature Selection Guidelines</h3>
"""
        
        if self.temperature_analysis:
            optimal_temp = self.temperature_analysis['optimal_temperature']['value']
            
            if optimal_temp <= 0.1:
                html_content += """            <p><strong>Conservative Planning:</strong> Use low temperatures (0.0-0.1) for maximum reliability and consistency.</p>"""
            elif optimal_temp <= 0.3:
                html_content += """            <p><strong>Balanced Performance:</strong> Moderate temperatures (0.1-0.3) provide good balance of reliability and flexibility.</p>"""
            else:
                html_content += """            <p><strong>Creative Planning:</strong> Higher temperatures may be beneficial for complex, creative problem-solving scenarios.</p>"""
        
        html_content += f"""        </div>
        
        <div class="warning">
            <h3>⚠️ Important Considerations</h3>
            <ul>
                <li>Temperature effects may vary significantly across different domains</li>
                <li>Consider domain complexity when selecting temperature</li>
                <li>{f"Single run per condition (exploratory analysis)" if self.metadata.get('runs_per_condition', 1) == 1 else f"{self.metadata.get('runs_per_condition', 'Multiple')} runs per condition for robust assessment"}</li>
                <li>Monitor both success rate and consistency metrics</li>
            </ul>
        </div>
        
        <h3>📋 Future Research Directions</h3>
        <ul>
            <li>Fine-grained analysis around optimal temperature range</li>
            <li>Investigation of temperature × prompt modality interactions</li>
            <li>Adaptive temperature strategies based on problem complexity</li>
            <li>Long-term consistency analysis across multiple sessions</li>
        </ul>
    </div>

    <div class="section">
        <h2>📚 Methodology</h2>
        <p><strong>Model:</strong> Phi4 (14B parameters)</p>
        <p><strong>Experimental Design:</strong> Controlled temperature variation with fixed other parameters</p>
        <p><strong>Analysis Methods:</strong> {f"Descriptive statistics, trend analysis" if self.metadata.get('runs_per_condition', 1) == 1 else "ANOVA, correlation analysis, descriptive statistics"}</p>
        <p><strong>Validation:</strong> PDDL plan validation using VAL validator</p>
        <p><strong>Replication:</strong> {f"Single run per condition (exploratory study)" if self.metadata.get('runs_per_condition', 1) == 1 else f"{self.metadata.get('runs_per_condition', 'Multiple')} runs per condition for statistical robustness"}</p>
    </div>

</body>
</html>"""
        
        # Save report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📋 Temperature analysis report saved: {report_file}")
        return str(report_file)


def main():
    """Main entry point for temperature analysis."""
    parser = argparse.ArgumentParser(description="Temperature Sensitivity Analysis Tool")
    parser.add_argument("experiment_dir", help="Temperature experiment directory")
    parser.add_argument("--analyze-only", action='store_true', help="Run analysis without generating report")
    parser.add_argument("--visualizations-only", action='store_true', help="Generate only visualizations")
    parser.add_argument("--report-only", action='store_true', help="Generate only report")
    
    args = parser.parse_args()
    
    try:
        print("🌡️ Temperature Sensitivity Analysis Tool")
        print("=" * 50)
        
        analyzer = TemperatureAnalyzer(args.experiment_dir)
        
        # Load results
        analyzer.load_temperature_results()
        
        if analyzer.results_df.empty:
            print("❌ No valid results found for analysis")
            return
        
        if args.visualizations_only:
            viz_files = analyzer.create_temperature_visualizations()
            print("🎨 Visualizations created:")
            for name, path in viz_files.items():
                print(f"  {name}: {path}")
        
        elif args.analyze_only:
            analysis = analyzer.analyze_temperature_effects()
            
            # Save analysis results
            analysis_file = analyzer.analysis_dir / 'temperature_analysis_results.json'
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            print(f"📊 Analysis results saved: {analysis_file}")
        
        else:
            # Full analysis and report generation
            analysis = analyzer.analyze_temperature_effects()
            report_file = analyzer.generate_temperature_report()
            
            print(f"\n🎉 Temperature analysis complete!")
            print(f"📋 Report: {report_file}")
            
            if 'optimal_temperature' in analysis:
                opt_temp = analysis['optimal_temperature']
                print(f"\n🎯 Key Result: Optimal temperature = {opt_temp['value']} (Success: {opt_temp['success_rate']:.1%})")
    
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()