# Models Directory

This directory contains the large language model weights used by the LLM-Needs-a-Plan framework for PDDL planning tasks.

## Available Models

### Llama4 (`Llama4/`)
- **Type**: Meta's Llama 4 model
- **Size**: ~107.8B parameters (202.4 GB on disk)
- **Files**: 50 model shards + configuration files
- **Status**: ✅ Ready for use
- **Memory Requirements**: 
  - GPU: 24GB+ VRAM recommended
  - CPU: 32GB+ RAM (slower inference)

**Key Files:**
```
Llama4/
├── config.json                    # Model configuration
├── tokenizer_config.json          # Tokenizer settings
├── tokenizer.json                 # Tokenizer vocabulary
├── model-00001-of-00050.safetensors  # Model weights (sharded)
├── ...
└── model-00050-of-00050.safetensors
```

### Phi4 (`Phi4/`)
- **Type**: Microsoft's Phi-4 model
- **Size**: ~14B parameters (27.3 GB on disk)
- **Files**: 6 model shards + configuration files
- **Status**: ✅ Ready for use
- **Memory Requirements**:
  - GPU: 16GB+ VRAM recommended
  - CPU: 16GB+ RAM (acceptable performance)

**Key Files:**
```
Phi4/
├── config.json                    # Model configuration
├── tokenizer_config.json          # Tokenizer settings  
├── tokenizer.json                 # Tokenizer vocabulary
├── model-00001-of-00006.safetensors  # Model weights (sharded)
├── ...
└── model-00006-of-00006.safetensors
```

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

# Force Llama4 model  
python3 src/main.py --model llama4
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

## Performance Notes

### Loading Time
- **Phi4**: ~30-60 seconds on SSD
- **Llama4**: ~2-5 minutes on SSD

### Inference Speed (CPU)
- **Phi4**: ~2-5 tokens/second
- **Llama4**: ~0.5-2 tokens/second

### Inference Speed (GPU)
- **Phi4**: ~20-50 tokens/second (depends on VRAM)
- **Llama4**: ~10-30 tokens/second (depends on VRAM)

## Troubleshooting

### Model Loading Issues

**"Out of Memory" Error:**
```bash
# Try smaller model
python3 src/main.py --model phi4

# Or use CPU with smaller batch
python3 src/main.py --model phi4 --batch false
```

**"Model files not found":**
```bash
# Check model directory exists
ls -la src/models/

# Verify model structure
python3 src/tests/test_model_manager.py
```

**Slow loading on CPU:**
- This is expected - CPU inference is significantly slower
- Consider using a GPU-enabled system for better performance

## Adding New Models

To add a new model:

1. Create a new directory in `src/models/`
2. Ensure it has the required files:
   - `config.json`
   - `tokenizer_config.json` 
   - `tokenizer.json`
   - Model weights (`.safetensors` files)
3. The ModelManager will automatically detect and support it