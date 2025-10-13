# LLM-Needs-a-Plan Experiment Framework

This directory contains a comprehensive framework for running systematic experiments on Large Language Models for automated planning tasks. The framework supports multi-model comparisons across different PDDL domains with automated resource management and result analysis.

## 📁 Directory Structure

```
experiments/
├── configs/
│   └── experiment_config.yml     # Main configuration file
├── scripts/                      # Generated SLURM job scripts
├── results/                      # Experiment outputs and results
├── logs/                        # SLURM job logs and monitoring data
├── generate_experiments.py      # Experiment generation tool
├── monitor_experiments.py       # Monitoring and analysis tool
└── README.md                    # This file
```

## ⚙️ Configuration

### Experiment Configuration (`configs/experiment_config.yml`)

The main configuration file defines:

- **Global Settings**: Cluster configuration, paths, resource limits
- **Models**: Available models with GPU requirements and generation parameters
- **Domains**: PDDL domains with associated problems and complexity ratings
- **Experiment Sets**: Pre-defined experiment combinations with priorities
- **Execution Settings**: Concurrency limits, retry policies, validation options

#### Example Configuration Structure:

```yaml
global:
  cluster:
    partition: "boost_usr_prod"
    account: "cin_staff"
    time_limit: "02:00:00"

models:
  phi4:
    name: "Phi4"
    path: "src/models/Phi4"
    gpus: 1
    generation_config:
      temperature: 0.1
      max_new_tokens: 2048

domains:
  tetris:
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