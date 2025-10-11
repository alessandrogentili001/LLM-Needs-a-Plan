"""
Model Manager for LLM Integration

Manages loading and interaction with large language models (Llama 4, Phi-4, etc.)
for PDDL planning tasks. Handles model loading, tokenization, and response generation.
"""

import os
import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import utilities with proper error handling
try:
    from ..utils.validator import validate_plan_from_text
    from ..utils.answer_postprocessor import formatter
    from ..core.file_manager import FileManager
    from ..prompts.prompts import system_prompt_pddl
except ImportError:
    # Fallback imports for when run directly
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.utils.validator import validate_plan_from_text
    from src.utils.answer_postprocessor import formatter
    from src.core.file_manager import FileManager
    from src.prompts.prompts import system_prompt_pddl

# Set transformers logging to warning to reduce output
logging.set_verbosity_warning()


class ModelManager:
    """
    Manages loading and interaction with large language models.
    
    Supports:
    - Llama 4 models (with gating/authorization)
    - Phi-4 models (public access)
    - Dynamic model detection based on path
    - GPU/CPU device management
    - Response generation with various parameters
    """

    def __init__(self, weights_path: str):
        """
        Initialize the ModelManager with model path.

        Args:
            weights_path (str): Path to the model weights directory
        """
        self.weights_path = weights_path
        self.model = None
        self.tokenizer = None
        self.file_manager = FileManager()
        self.device = None
        self.model_type = self._detect_model_type(weights_path)
        
        print(f"Detected model type: {self.model_type}")

    def _detect_model_type(self, weights_path: str) -> str:
        """
        Detect model type from weights path.
        
        Args:
            weights_path (str): Path to model weights
            
        Returns:
            str: Model type ('phi4', 'llama4', 'unknown')
        """
        path_lower = weights_path.lower()
        
        if 'phi' in path_lower or 'phi-4' in path_lower or 'phi4' in path_lower:
            return 'phi4'
        elif 'llama' in path_lower or 'llama-4' in path_lower or 'llama4' in path_lower:
            return 'llama4'
        else:
            return 'unknown'

    def load(self) -> Tuple[Any, Any]:
        """
        Load the model and tokenizer.

        Returns:
            Tuple[Any, Any]: (model, tokenizer) loaded and ready to use
            
        Raises:
            SystemExit: If model loading fails
        """
        # Check device availability
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        device_info = "GPU" if torch.cuda.is_available() else "CPU"
        
        print(f"CUDA {'is' if torch.cuda.is_available() else 'is not'} available. Using {device_info}.")
        
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

        try:
            print(f"Loading model from: {self.weights_path}")
            
            # Load model with appropriate configuration
            model_kwargs = {
                "device_map": "auto",
                "torch_dtype": torch.bfloat16,
                "trust_remote_code": True,  # Some models may require this
            }
            
            # Adjust loading parameters based on model type
            if self.model_type == 'phi4':
                model_kwargs.update({
                    "attn_implementation": "flash_attention_2" if torch.cuda.is_available() else None
                })
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.weights_path,
                **{k: v for k, v in model_kwargs.items() if v is not None}
            )
            
            # Load tokenizer
            tokenizer_kwargs = {
                "padding_side": "left",  # For batch generation
                "trust_remote_code": True,
            }
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.weights_path,
                **tokenizer_kwargs
            )
            
            # Set pad token if not exists
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            print(f"Model loaded successfully")
            print(f"Model parameters: ~{sum(p.numel() for p in self.model.parameters()) / 1e9:.1f}B")
            
            return self.model, self.tokenizer
            
        except Exception as e:
            print(f"Error loading model: {e}")
            print(f"Make sure:")
            print(f"  1. Path exists: {os.path.exists(self.weights_path)}")
            print(f"  2. You have access to the model")
            print(f"  3. Sufficient GPU memory available")
            sys.exit(1)

    def generate_response(
        self,
        prompt: str,
        max_tokens: int = 5000,
        add_system_prompt: bool = True,
        sampling: bool = False,
        temperature: float = 0.6,
        top_k: int = 10,
        include_prompt: bool = True,
        skip_special_tokens: bool = True,
    ) -> str:
        """
        Generate a response using the loaded model.

        Args:
            prompt (str): Input prompt for the model
            max_tokens (int): Maximum number of tokens to generate
            add_system_prompt (bool): Whether to add system prompt
            sampling (bool): Whether to use sampling for generation
            temperature (float): Temperature for sampling (only used if sampling=True)
            top_k (int): Top-k for sampling (only used if sampling=True)
            include_prompt (bool): Whether to include prompt in output
            skip_special_tokens (bool): Whether to skip special tokens in output

        Returns:
            str: Generated response text
            
        Raises:
            ValueError: If model/tokenizer not loaded
        """
        if not self.model or not self.tokenizer:
            raise ValueError("Model and tokenizer must be loaded before generating responses")

        # Prepare messages
        if add_system_prompt:
            messages = [
                {"role": "system", "content": system_prompt_pddl},
                {"role": "user", "content": prompt},
            ]
        else:
            messages = [{"role": "user", "content": prompt}]

        # Format messages using chat template
        try:
            formatted_message = self.tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
        except Exception as e:
            print(f"Warning: Chat template failed ({e}), using direct prompt")
            formatted_message = f"{system_prompt_pddl}\n\nUser: {prompt}\n\nAssistant:" if add_system_prompt else prompt

        # Tokenize input
        inputs = self.tokenizer(
            formatted_message, 
            return_tensors="pt", 
            truncation=True,
            max_length=4000  # Leave room for generation
        ).to(self.model.device)

        # Generation parameters
        generation_config = {
            "max_new_tokens": max_tokens,
            "do_sample": sampling,
            "eos_token_id": self.tokenizer.eos_token_id,
            "pad_token_id": self.tokenizer.pad_token_id,
            "use_cache": True,
        }
        
        if sampling:
            generation_config.update({
                "temperature": temperature,
                "top_k": top_k,
                "top_p": 0.9,
            })
        else:
            generation_config.update({
                "temperature": 0.0,
                "do_sample": False,
            })

        # Generate response
        try:
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    **generation_config
                )

            # Extract and decode response
            if include_prompt:
                response_tokens = outputs[0]
            else:
                response_tokens = outputs[0][inputs["input_ids"].shape[1]:]

            response = self.tokenizer.decode(
                response_tokens, 
                skip_special_tokens=skip_special_tokens
            )
            
            return response.strip()
            
        except Exception as e:
            print(f"Error during generation: {e}")
            return f"Generation failed: {str(e)}"

    def iterative_planning_with_validation(
        self,
        domain_path: str,
        problem_path: str,
        initial_prompt: str,
        max_iterations: int = 3,
        **generation_kwargs
    ) -> Tuple[str, int, bool]:
        """
        Generate plan with iterative validation and correction.
        
        Args:
            domain_path (str): Path to PDDL domain file
            problem_path (str): Path to PDDL problem file
            initial_prompt (str): Initial prompt for plan generation
            max_iterations (int): Maximum number of validation iterations
            **generation_kwargs: Additional arguments for generate_response
            
        Returns:
            Tuple[str, int, bool]: (final_response, iterations_used, is_valid)
        """
        messages = [
            {"role": "system", "content": system_prompt_pddl},
            {"role": "user", "content": initial_prompt}
        ]
        
        for iteration in range(max_iterations):
            print(f"Planning iteration {iteration + 1}/{max_iterations}")
            
            # Format current conversation
            conversation_text = self._format_conversation(messages)
            
            # Generate response
            response = self.generate_response(
                conversation_text,
                add_system_prompt=False,  # Already in conversation
                include_prompt=False,
                **generation_kwargs
            )
            
            # Extract and validate plan
            formatted_response = formatter(response, include_reasoning=True)
            plan_actions = formatted_response.get("plan", [])
            
            if not plan_actions:
                # Add feedback for empty plan
                messages.extend([
                    {"role": "assistant", "content": response},
                    {"role": "user", "content": "The response doesn't contain a valid plan. Please provide a clear sequence of PDDL actions to solve the problem."}
                ])
                continue
            
            # Create temporary plan text for validation
            plan_text = "\n".join(plan_actions)
            
            # Validate plan
            validation_result = validate_plan_from_text(domain_path, problem_path, plan_text)
            
            if validation_result.get("valid", False):
                print(f"Valid plan found in {iteration + 1} iterations")
                return response, iteration + 1, True
            
            # Plan is invalid, provide feedback
            error_msg = validation_result.get("error", "Plan validation failed")
            feedback = f"The plan is invalid. Error: {error_msg}. Please provide a corrected plan."
            
            messages.extend([
                {"role": "assistant", "content": response},
                {"role": "user", "content": feedback}
            ])
            
            print(f"Invalid plan (iteration {iteration + 1}): {error_msg}")
        
        print(f"No valid plan found after {max_iterations} iterations")
        return response, max_iterations, False

    def _format_conversation(self, messages: List[Dict]) -> str:
        """
        Format conversation messages into a single prompt.
        
        Args:
            messages (List[Dict]): List of conversation messages
            
        Returns:
            str: Formatted conversation text
        """
        conversation_parts = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                conversation_parts.append(f"System: {content}")
            elif role == "user":
                conversation_parts.append(f"User: {content}")
            elif role == "assistant":
                conversation_parts.append(f"Assistant: {content}")
        
        conversation_parts.append("Assistant:")  # Prompt for next response
        return "\n\n".join(conversation_parts)

    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dict: Model information
        """
        if not self.model:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "model_type": self.model_type,
            "weights_path": self.weights_path,
            "device": str(self.device),
            "parameters": f"~{sum(p.numel() for p in self.model.parameters()) / 1e9:.1f}B",
            "torch_dtype": str(self.model.dtype) if hasattr(self.model, 'dtype') else "unknown",
            "vocab_size": self.tokenizer.vocab_size if self.tokenizer else "unknown"
        }