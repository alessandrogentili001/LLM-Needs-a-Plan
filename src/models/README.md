# Models Directory

This directory contains the large language model weights used by the LLM-Needs-a-Plan framework for PDDL planning tasks.

## Available Models

### Llama3 (`Llama3/`)
- **Type**: Meta's Llama 3.1 model
- **Size**: ~8B parameters
- **Memory Requirements**: 16GB+ VRAM recommended
- **Link**: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct

### Phi4 (`Phi4/`)
- **Type**: Microsoft's Phi-4-reasoning model
- **Size**: ~14B parameters
- **Memory Requirements**: 32GB+ VRAM recommended
- **Link**: https://huggingface.co/microsoft/Phi-4-reasoning

### Gemma3 (`Gemma3/`)
- **Type**: Google's Gemma-3 model
- **Size**: ~27B parameters
- **Memory Requirements**: 48GB+ VRAM recommended
- **Link**: https://huggingface.co/google/gemma-3-27b-it

## Model Selection

### Automatic Selection
The framework automatically detects and selects models based on the path:

```bash
# Auto-select from models directory
python3 src/main.py --weights_path src/models

# Specify exact model
python3 src/main.py --weights_path src/models/Phi4
```

### Manual Selection
You can specify which model to use:

```bash
# Force Phi4 model
python3 src/main.py --model phi4

# Force Llama3 model  
python3 src/main.py --model llama3

# Force Gemma3 model 
python3 src/main.py --model Gemma3
```

## Model Loading

Models are loaded automatically by the ModelManager:

```python
from core.model_manager import ModelManager

# Initialize model manager
mm = ModelManager("src/models/Phi4")

# Load model (this takes time and memory)
model, tokenizer = mm.load()

# Model is now ready for inference
```

## Configuration

Models integrate with the configuration system via `config.yml`:

```yaml
MODEL_PATH: "src/models"          # Base models directory
# Or specify exact model:
# MODEL_PATH: "src/models/Phi4"
```

## Adding New Models

To add a new model:

1. Create a new directory in `src/models/`
2. Ensure it has the required files:
   - `config.json`
   - `tokenizer_config.json` 
   - `tokenizer.json`
   - Model weights (`.safetensors` files)
3. The ModelManager will automatically detect and support it