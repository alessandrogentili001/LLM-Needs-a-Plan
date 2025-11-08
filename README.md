# Emergent Capabilities of LLMs: Meta-Evaluation of Planning and Reasoning in Large Language Models

## Authors
- **Alessandro Gentili** - *AI Student @UniBo* - [GitHub](https://github.com/alessandrogentili001)
- **Lorenzo D'Ascenzo** - *AI Student @UniBo* - [GitHub](https://github.com/Lorenzo00dash)

## Abstract

This project extends previous work by our colleagues [Merola, Sigh, and Dardouri](https://dvcs.apice.unibo.it/pika-lab/courses/ai-ethics/projects/merolasinghdardouri2425) on evaluating LLM performance in planning tasks and developing a meta-network for reliability prediction. The proposed extensions focus on two directions: (1) exploring emergent reasoning capabilities across a broader range of open-source large language models, including Mistral, LLaMA, and DeepSeek, to assess whether planning abilities generalize across architectures; and (2) enriching the benchmark dataset with new, challenging planning problems of graded complexity. Together, these extensions aim to deepen our understanding of LLM reasoning, improve evaluation reliability, and foster reproducible benchmarks for the research community.

## Disclaimer

The correct execution of experiments in this project requires substantial computational resources. The majority of our experimental work will be conducted using the **Leonardo supercomputer cluster node** provided by [CINECA](https://www.cineca.it/), one of the most powerfull supercomputing centers. 
Access to Leonardo's computational capabilities enables us to perform experiments that would be infeasible on standard computing hardware, ensuring the reproducibility and scalability of our research findings.

## Documentation

### Repository Structure 

### Papers

Two papers inspired this work:

- [Paper 1](assets/2407.11511v1.pdf)
- [Paper 2](assets/2406.05572v2.pdf)

We recommend the reading of the above mentioned papers in order to get a higher viewpoint on the whole methodology applied in this project.

### Leonardo

An official guide to the cluster login and setup is provided:

- [Leonardo Guide](assets/Guida%20Leonardo.pdf)

Additional step-by-step tutorials about the configuration, setup and usage of the Leonardo cluster are added in the following guides:

- [Pre-Configuration Steps](assets/1.%20Pre%20Configuration.md)  
- [Cluster Node Configuration](assets/2.%20Cluster%20Set%20Up.md)  
- [First Job Submission](assets/3.%20Load%20Local%20Files%20Into%20The%20Cluster.md)  
- [File Transfer Guide](assets/4.%20First%20Job%20Submission.md) 
- [Work Directory And LLMs Download](assets/5.%20Work%20Directory%20And%20LLMs%20Download.md)

### Problems

The planning problems, written in PPDL language, are taken from this [repository](https://github.com/potassco/pddl-instances), where a description and multiple instances are provided for each problem. In particular we have selected a couple of them:

- [Tetris](https://github.com/potassco/pddl-instances/tree/master/ipc-2014/domains/tetris-sequential-satisficing)
- [City Car](https://github.com/potassco/pddl-instances/tree/master/ipc-2014/domains/city-car-sequential-satisficing)

Each of the selected probelms comes with a list of instances at different scale and complexity. 

### Models

This project utilizes three state-of-the-art large language models to evaluate and compare their planning and reasoning capabilities. The selection provides a comprehensive analysis across different model sizes and architectures, from compact efficiency to high-capacity reasoning:

- **[Llama 3.1 8B Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)** - Meta's efficient 8B parameter model, optimized for instruction following with good balance of speed and performance.

- **[Phi-4](https://huggingface.co/microsoft/Phi-4)** - Microsoft's 14B parameter reasoning-optimized model, designed for complex problem-solving and planning tasks with superior reasoning capabilities.

- **[Gemma-3 27B IT](https://huggingface.co/google/gemma-3-27b-it)** - Google's high-capacity 27B parameter model with advanced instruction-tuning, providing state-of-the-art performance on reasoning benchmarks.

All models are freely available on Hugging Face (Llama 3.1 requires accepting Meta's license agreement).

### Tests

Small scripts are added [here](src/tests) to test things on an ongoing basis.

### Validator

You can find the planning validator [here](https://github.com/KCL-Planning/VAL?utm_source=chatgpt.com).

## Getting Started

### Prerequisites

### Installation

### Running Experiments

