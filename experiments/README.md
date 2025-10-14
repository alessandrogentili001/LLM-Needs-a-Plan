# 🧠 Phi4 Planning Research Framework

This directory contains an advanced research framework for systematic exploration of Phi4 model capabilities in automated planning. The framework focuses on understanding model reasoning patterns, parameter sensitivity, and emergent capabilities through structured experiments.

## 🎯 Research Focus

The framework is designed to investigate:

- **Parameter Sensitivity**: How generation parameters affect planning performance
- **Prompt Engineering**: Effectiveness of different prompting strategies  
- **Reasoning Emergence**: Development of planning capabilities through iterations
- **Domain Generalization**: Model performance across different planning complexity levels

## 📁 Directory Structure

```
experiments/
├── configs/
│   └── experiment_config.yml          # Research configuration file
├── results/                           # Organized experiment results
│   ├── parameter_sensitivity/         # Parameter exploration results
│   ├── prompt_engineering/           # Prompt modality comparisons
│   ├── iterative_reasoning/          # Multi-iteration experiments
│   ├── configurations/               # Generated experiment configs
│   ├── analysis/                     # Analysis outputs and reports
│   └── metadata/                     # Experiment tracking data
├── templates/                        # Experiment templates
├── phi4_research_generator.py        # Research experiment generator
├── phi4_research_analyzer.py         # Advanced analysis tool
├── run_experiment.py                 # Single experiment runner
├── analyze_results.py                # General analysis tool
└── README.md                         # This file
```

## 🔬 Research Configuration

### Core Research Elements

The `experiment_config.yml` defines a comprehensive research framework:

#### 1. **Research Metadata**
```yaml
research:
  project_title: "Phi4 Reasoning Capabilities in Automated Planning"
  research_questions:
    - "How do different prompt modalities affect planning performance?"
    - "What is the optimal temperature for planning tasks?"
    - "Does iterative prompting improve plan quality?"
```

#### 2. **Advanced Prompt Modalities**
- **Direct Planning**: Straightforward problem-solution prompting
- **Chain-of-Thought**: Step-by-step reasoning approach
- **Few-Shot Learning**: Learning from examples
- **Self-Reflection**: Generate-validate-improve cycle
- **Adversarial Validation**: Challenge and refine plans

#### 3. **Parameter Exploration Space**
```yaml
parameter_space:
  temperature:
    values: [0.0, 0.1, 0.3, 0.5, 0.7, 0.9]
    hypothesis: "Lower temperatures yield more precise plans"
  
  top_p:
    values: [0.8, 0.9, 0.95, 1.0]
    hypothesis: "Moderate top_p balances quality and diversity"
```

#### 4. **Research Experiments**
- **Parameter Sensitivity**: Systematic parameter exploration
- **Prompt Engineering**: Comparative prompting strategy analysis
- **Iterative Reasoning**: Multi-turn reasoning capabilities

## 🚀 Getting Started

### 1. Quick Research Experiment

```bash
# Generate parameter sensitivity experiments
cd experiments/
python phi4_research_generator.py --experiment-types parameter_sensitivity

# Run a single experiment
python run_experiment.py run-set parameter_sensitivity

# Analyze results
python phi4_research_analyzer.py --generate-report
```

### 2. Custom Research Setup

```bash
# Preview what experiments would be generated
python phi4_research_generator.py --dry-run

# Generate specific experiment type
python phi4_research_generator.py --experiment-types prompt_engineering

# Monitor and analyze
python phi4_research_analyzer.py --experiment-types prompt_engineering
```

## 🔧 Research Tools

### Experiment Generation (`phi4_research_generator.py`)

Advanced generator for research-focused experiments:

```bash
# Generate all research experiments
python phi4_research_generator.py

# Generate specific research area
python phi4_research_generator.py --experiment-types parameter_sensitivity prompt_engineering

# Dry run to preview experiments  
python phi4_research_generator.py --dry-run
```

**Features:**
- Automatic parameter combination generation
- Structured result organization
- Research metadata tracking
- Configuration-result linking

### Research Analysis (`phi4_research_analyzer.py`)

Comprehensive analysis tool for research insights:

```bash
# Generate full research report
python phi4_research_analyzer.py --generate-report

# Create visualizations only
python phi4_research_analyzer.py --visualizations-only

# Analyze specific experiment types
python phi4_research_analyzer.py --experiment-types parameter_sensitivity
```

**Analysis Capabilities:**
- Parameter sensitivity analysis with correlation studies
- Prompt effectiveness comparative statistics
- Emergent capability pattern recognition
- Statistical significance testing
- Research visualization generation

## 📊 Research Insights

### Parameter Sensitivity Analysis

The framework analyzes how generation parameters affect:
- Plan validity and executability
- Generation time and efficiency  
- Reasoning coherence and quality
- Success rates across domains

### Prompt Engineering Effectiveness

Comparative analysis includes:
- Success rate comparisons across modalities
- Statistical significance testing
- Domain-specific effectiveness patterns
- Reasoning quality metrics

### Emergent Capabilities

Investigation of:
- Reasoning pattern development
- Iterative improvement capabilities
- Complexity scaling behavior
- Transfer learning across domains

## 🎯 Research Applications

### Academic Research

The framework supports:
- **Publication-ready analysis**: Statistical tests, visualizations, comprehensive reports
- **Reproducible experiments**: Complete configuration tracking and version control
- **Systematic exploration**: Structured parameter space exploration
- **Comparative studies**: Multi-modal and multi-parameter comparisons

### Model Development

Research insights for:
- **Parameter tuning**: Data-driven optimization recommendations  
- **Prompt optimization**: Evidence-based prompting strategies
- **Capability assessment**: Understanding model strengths and limitations
- **Scaling analysis**: Performance prediction for different configurations

## 📋 Result Organization

### Hierarchical Structure

Results are organized as:
```
results/
└── {experiment_type}/
    └── {prompt_modality}/
        └── {parameter_hash}/
            └── {domain}/
                ├── experiment_config.json
                ├── results.json
                └── analysis.json
```

### Metadata Tracking

Each experiment includes:
- **Configuration ID**: Unique experiment identifier
- **Parameter Hash**: Reproducibility tracking
- **Research Context**: Link to research questions
- **Execution Metadata**: Timestamps, versions, environment info

## 🔍 Advanced Features

### Automatic Linking System

- **Config-to-Results**: Automatic linking between configurations and results
- **Parameter Tracking**: Hash-based parameter combination identification
- **Version Control**: Experiment versioning and reproducibility
- **Research Context**: Research question mapping to experiments

### Quality Control

- **Validation Pipeline**: Automatic result validation
- **Statistical Significance**: Built-in statistical testing
- **Anomaly Detection**: Identification of unusual results
- **Manual Review Triggers**: Alerts for results requiring investigation

## 📚 Best Practices

### Research Planning

1. **Start Small**: Begin with parameter_sensitivity quick tests
2. **Iterate**: Use insights from initial experiments to design follow-ups
3. **Document**: Maintain clear research questions and hypotheses
4. **Validate**: Use statistical testing for robust conclusions

### Experiment Design

1. **Control Variables**: Systematic parameter variation
2. **Statistical Power**: Ensure sufficient sample sizes
3. **Reproducibility**: Use consistent random seeds and configurations
4. **Baseline Comparison**: Always include baseline conditions

### Analysis and Reporting

1. **Multiple Metrics**: Consider various performance dimensions
2. **Statistical Rigor**: Apply appropriate statistical tests
3. **Visualization**: Create clear, publication-ready plots
4. **Interpretation**: Connect results back to research questions

## 🚀 Future Extensions

The framework is designed for extensibility:

- **Additional Models**: Easy integration of new models beyond Phi4
- **New Domains**: Support for additional PDDL domains and complexity levels
- **Advanced Prompting**: Integration of novel prompting techniques
- **Real-time Analysis**: Live experiment monitoring and adaptive parameter selection

## 📞 Support and Documentation

For detailed information:
- See `templates/` for experiment template examples
- Check `configs/experiment_config.yml` for configuration reference
- Review generated reports for analysis methodology
- Examine `phi4_research_*.py` scripts for implementation details
    name: "Tetris"
    domain_file: "tetris-domain.pddl"
    problems: ["tetris01.pddl", "tetris02.pddl", ...]

experiment_sets:
  quick_test:
    description: "Quick validation test"
    models: ["phi4"]
    domains: ["tetris"]
    problem_limit: 2
    priority: 1
```

## 🚀 Getting Started

### 1. Generate Experiments

Create SLURM job scripts for a specific experiment set:

```bash
# Generate scripts for quick test
./experiments/generate_experiments.py -c experiments/configs/experiment_config.yml -e quick_test

# Generate scripts for comprehensive comparison
./experiments/generate_experiments.py -c experiments/configs/experiment_config.yml -e model_comparison
```

This creates:
- Individual SLURM scripts for each experiment
- Batch submission script
- Monitoring script
- Experiment metadata

### 2. Submit Experiments

Run the generated batch script to submit all experiments:

```bash
# Submit all experiments in the set
./experiments/scripts/submit_quick_test.sh

# Or submit individual experiments
sbatch experiments/scripts/quick_test_phi4_tetris_tetris01.sh
```

### 3. Monitor Progress

Track experiment progress in real-time:

```bash
# Interactive monitoring (updates every 30 seconds)
./experiments/monitor_experiments.py -e quick_test --watch

# Generate one-time report with visualizations
./experiments/monitor_experiments.py -e quick_test --visualize

# Monitor all experiments
./experiments/monitor_experiments.py --visualize
```

## 📊 Experiment Sets

### Pre-defined Experiment Sets:

1. **`quick_test`**: Fast validation with Phi4 on 2 Tetris problems
2. **`model_comparison`**: Compare Phi4 vs Llama4 on Tetris and Blocks domains
3. **`domain_analysis`**: Full domain coverage with Phi4 across all domains
4. **`comprehensive`**: Complete matrix - all models on all domains

### Custom Experiment Sets:

Add new experiment sets to `experiment_config.yml`:

```yaml
experiment_sets:
  my_custom_test:
    description: "Custom experiment description"
    models: ["phi4"]
    domains: ["logistics"]
    problem_limit: 5
    priority: 2
```

## 🔬 Results and Analysis

### Generated Output:

Each experiment produces:
- `experiment_results.json`: Detailed results with metrics
- `generated_plan.txt`: The generated PDDL plan
- `validation_output.txt`: VAL validator output
- `generation_log.txt`: Model generation details

### Monitoring Reports:

The monitor generates:
- **JSON Reports**: Machine-readable experiment status
- **Text Summaries**: Human-readable progress reports  
- **Visualizations**: Success rates, performance metrics, resource usage
- **Real-time Status**: Live job queue monitoring

### Key Metrics:

- **Plan Validity**: Whether generated plans are syntactically and semantically correct
- **Plan Length**: Number of actions in generated plans
- **Generation Time**: Time taken for model inference
- **Success Rate**: Percentage of problems solved correctly
- **Resource Usage**: GPU memory, compute time, storage

## 🛠️ Advanced Usage

### Resource Management:

The framework automatically:
- Allocates appropriate GPU resources based on model size
- Manages concurrent job limits to prevent resource contention
- Implements priority-based scheduling for experiment sets
- Provides automatic retry for failed jobs

### GPU Configuration:

- **Phi4 (14B)**: 1 GPU, 40GB memory
- **Llama4 (107B)**: 4 GPUs, 320GB total memory
- Automatic `CUDA_VISIBLE_DEVICES` management

### Cluster Integration:

Designed for Leonardo cluster with:
- SLURM job scheduler
- NVIDIA A100 GPUs
- Module system integration
- Proper account and partition handling

## 📝 Example Workflow

### Complete Experiment Pipeline:

```bash
# 1. Configure experiments
vim experiments/configs/experiment_config.yml

# 2. Generate experiment scripts
./experiments/generate_experiments.py -c experiments/configs/experiment_config.yml -e model_comparison

# 3. Review generated scripts
ls experiments/scripts/

# 4. Submit experiments  
./experiments/scripts/submit_model_comparison.sh

# 5. Monitor progress
./experiments/monitor_experiments.py -e model_comparison --watch

# 6. Generate analysis report
./experiments/monitor_experiments.py -e model_comparison --visualize

# 7. Review results
ls experiments/results/
```

### Typical Output Structure:

```
experiments/
├── scripts/
│   ├── model_comparison_phi4_tetris_tetris01.sh
│   ├── model_comparison_llama4_tetris_tetris01.sh
│   ├── submit_model_comparison.sh
│   └── monitor_model_comparison.sh
├── results/
│   ├── model_comparison_phi4_tetris_tetris01/
│   │   ├── experiment_results.json
│   │   ├── generated_plan.txt
│   │   └── validation_output.txt
│   └── model_comparison_llama4_tetris_tetris01/
└── logs/
    ├── model_comparison_phi4_tetris_tetris01_12345.out
    └── model_comparison_phi4_tetris_tetris01_12345.err
```

## 🎯 Best Practices

### Experiment Design:

1. **Start Small**: Use `quick_test` to validate setup before large experiments
2. **Resource Planning**: Consider GPU availability for concurrent jobs
3. **Problem Selection**: Use `problem_limit` to control experiment scope
4. **Priority Management**: Set appropriate priorities for experiment sets

### Monitoring:

1. **Regular Checks**: Monitor experiments periodically using the watch mode
2. **Log Analysis**: Check SLURM logs for debugging failed experiments
3. **Resource Tracking**: Monitor GPU and storage usage
4. **Result Validation**: Verify plan validity using integrated VAL validator

### Result Analysis:

1. **Systematic Comparison**: Use consistent metrics across experiments
2. **Statistical Significance**: Run multiple trials for robust results
3. **Visualization**: Generate plots for easy interpretation
4. **Data Preservation**: Archive completed experiments for reproducibility

## 🔧 Troubleshooting

### Common Issues:

1. **GPU Out of Memory**: Reduce batch size or use smaller model
2. **Job Queue Full**: Reduce `concurrent_jobs` in config
3. **Missing Dependencies**: Check module loading in SLURM scripts
4. **Path Errors**: Verify all paths are absolute and accessible on cluster

### Debug Commands:

```bash
# Check job status
squeue -u $USER

# View job logs
cat experiments/logs/experiment_name_jobid.err

# Check experiment results
ls experiments/results/experiment_name/

# Validate experiment configuration
python3 -c "import yaml; print(yaml.safe_load(open('experiments/configs/experiment_config.yml')))"
```

## 📈 Performance Optimization

### Cluster Efficiency:

- Use appropriate node types for different model sizes
- Balance concurrent jobs vs. resource availability  
- Implement intelligent job scheduling based on priorities
- Monitor resource utilization and adjust accordingly

### Model Optimization:

- Configure generation parameters for optimal performance
- Use FlashAttention2 when available for memory efficiency
- Implement gradient checkpointing for large models
- Consider model quantization for resource-constrained environments

## 🔄 Integration with Main Codebase

The experiment framework integrates seamlessly with the main LLM-Needs-a-Plan codebase:

- Uses existing `src/main.py` CLI interface
- Leverages `src/core/` modules for processing
- Integrates with VAL validator via `src/utils/validator.py`
- Follows same configuration patterns as main application

This ensures consistency and allows easy extension of experiment capabilities as the main codebase evolves.