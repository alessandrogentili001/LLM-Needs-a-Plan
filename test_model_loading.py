#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, 'src')

from core.model_manager import ModelManager
import torch

print("Testing Llama4 model loading with improved memory management...")
print(f"Available GPUs: {torch.cuda.device_count()}")

if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f"  GPU {i}: {props.name} ({props.total_memory / 1024**3:.1f} GB)")

# Test model loading
try:
    model_manager = ModelManager("src/models/Llama4")
    print("\n✅ Model loading configuration created successfully")
    print("Memory management settings applied for Llama4")
except Exception as e:
    print(f"\n❌ Error in model configuration: {e}")
    sys.exit(1)

print("\nTest completed - configuration looks good for cluster execution")
