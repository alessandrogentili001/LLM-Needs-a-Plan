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
from typing import Dict, List, Optional, Tuple, Any, Callable

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
    - LLMs selection and loading
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
            str: Model type
        """
        path_lower = weights_path.lower()
        
        if 'phi' in path_lower:
            return 'phi4'
        elif 'llama' in path_lower:
            return 'llama3'
        elif 'gemma' in path_lower:
            return 'gemma3'
        elif 'kimi' in path_lower:
            return 'kimi'
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
            gpu_count = torch.cuda.device_count()
            print(f"Available GPUs: {gpu_count}")
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1e9
                print(f"  GPU {i}: {gpu_name} ({gpu_memory:.1f} GB)")
            
            total_memory = sum(torch.cuda.get_device_properties(i).total_memory 
                             for i in range(gpu_count)) / 1e9
            print(f"Total GPU Memory Available: {total_memory:.1f} GB")

        try:
            print(f"Loading model from: {self.weights_path}")
            
            # Configure multi-GPU setup
            gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
            
            # Load model with appropriate configuration
            model_kwargs = {
                "torch_dtype": torch.bfloat16,
                "trust_remote_code": True,
            }
            
            # Configure device mapping based on available GPUs (x1-4 Nvidia X100 64GB each)
            if gpu_count > 0:
                model_kwargs["device_map"] = "auto"
                print("Using single GPU with automatic mapping")
            else:
                model_kwargs["device_map"] = {"": self.device}
                print("Using CPU for model management")
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.weights_path,
                **{k: v for k, v in model_kwargs.items() if v is not None}
            )
            print(f"Model loaded onto {self.device}")
            
            # Load tokenizer
            # Tokenizer kwargs may be model-specific; default to empty dict to
            # avoid NameError when not provided.
            tokenizer_kwargs = globals().get('tokenizer_kwargs', {}) or {}
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.weights_path,
                **tokenizer_kwargs
            )
            print(f"Tokenizer loaded onto {self.device}")
                        
            print(f"Model loaded successfully")
            print(f"Model parameters: ~{sum(p.numel() for p in self.model.parameters()) / 1e9:.1f}B")
            
            return self.model, self.tokenizer
            
        except Exception as e:
            print(f"Error loading model: {e}")
            sys.exit(1)

    def generate_response(
        self,
        prompt: str,
        max_tokens: int,
        add_system_prompt: bool,
        sampling: bool,
        temperature: float,
        top_k: int,
        include_prompt: bool,
        skip_special_tokens: bool,
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
                {"role": "system", "content": system_prompt_pddl}, # system prompt 
                {"role": "user", "content": prompt},               # user prompt
            ]
        else:
            messages = [{"role": "user", "content": prompt}]

        # Format messages using chat template when available; otherwise fall back
        try:
            formatted_message = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        except Exception:
            # Some tokenizers/models don't implement apply_chat_template
            formatted_message = f"{system_prompt_pddl}\n\nUser: {prompt}\n\nAssistant:" if add_system_prompt else prompt

        # Tokenize input (respect tokenizer limits when available)
        model_max = getattr(self.tokenizer, "model_max_length", None) or 2048
        max_input_len = min(model_max, 4096)
        inputs = self.tokenizer(
            formatted_message,
            return_tensors="pt",
            truncation=True,
            max_length=max_input_len,
        )

        # Move inputs to the model device. Use model parameters to find device
        try:
            model_device = next(self.model.parameters()).device
        except Exception:
            model_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        inputs = {k: v.to(model_device) for k, v in inputs.items()}

        # Generation parameters
        generation_config = {
            "max_new_tokens": int(max_tokens),
            "do_sample": bool(sampling),
            "eos_token_id": self.tokenizer.eos_token_id,
            "pad_token_id": self.tokenizer.pad_token_id,
            "use_cache": True,
        }

        if sampling and temperature > 0:
            generation_config.update({
                "temperature": float(temperature),
                "top_k": int(top_k),
                "top_p": 0.9,
            })

        # Run generation and handle OOMs cleanly
        try:
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    **generation_config,
                )

            # outputs is a tensor (batch, seq_len) or a list-like
            if isinstance(outputs, (list, tuple)):
                out_tensor = outputs[0]
            else:
                out_tensor = outputs

            # Take first batch
            first = out_tensor[0]

            if include_prompt:
                response_tokens = first
            else:
                input_len = inputs["input_ids"].shape[1]
                response_tokens = first[input_len:]

            response = self.tokenizer.decode(
                response_tokens,
                skip_special_tokens=skip_special_tokens,
            )

            return response.strip()

        except RuntimeError as e:
            # OOM handling
            if "out of memory" in str(e).lower():
                msg = (
                    "CUDA out of memory during generation. "
                    "Try reducing --max_tokens, use a smaller model, or enable model parallelism."
                )
                print(msg)
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                return f"Generation failed: {msg}"
            else:
                print(f"Error during generation: {e}")
                return f"Generation failed: {str(e)}"

    def iterative_planning_with_validation(
        self,
        domain_path: str,
        problem_path: str,
        initial_prompt: str,
        max_iterations: int = 3,
        add_system_prompt: bool = True,
        validation_feedback_fn: Optional[Callable[[str, str, str], str]] = None,
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
        # Respect whether caller wants a system prompt included.
        if add_system_prompt:
            messages = [
                {"role": "system", "content": system_prompt_pddl},
                {"role": "user", "content": initial_prompt}
            ]
        else:
            messages = [{"role": "user", "content": initial_prompt}]
        
        for iteration in range(max_iterations):
            print(f"Planning iteration {iteration + 1}/{max_iterations}")
            
            # Format current conversation
            conversation_text = self._format_conversation(messages)

            # --- DEBUG LOGGING: write the exact conversation sent to the model ---
            try:
                # Write debug logs into the repository root `debug_prompts/` so they
                # are easy to find regardless of the current working directory used
                # by batch/cluster jobs.
                repo_root = Path(__file__).resolve().parents[2]
                dbg_dir = repo_root / "debug_prompts"
                print(f"[DEBUG] Attempting to write debug prompts to: {dbg_dir}")
                dbg_dir.mkdir(parents=True, exist_ok=True)
                problem_base = Path(problem_path).stem if problem_path else "unknown_problem"
                convo_file = dbg_dir / f"{problem_base}_conversation_iter{iteration+1}.txt"
                convo_file.write_text(conversation_text, encoding="utf-8")
            except Exception as e:
                # Do not fail the planning loop due to logging issues but surface debug info
                print(f"[DEBUG] Failed to write conversation log: {e}")
                pass
            
            # Generate response
            # Remove conflicting arguments from generation_kwargs
            filtered_kwargs = {k: v for k, v in generation_kwargs.items()
                               if k not in ['add_system_prompt', 'include_prompt']}

            # Ensure required generation parameters exist and provide safe defaults
            defaults = {
                "max_tokens": 5000,
                "sampling": False,
                "temperature": 0.0,
                "top_k": 50,
                "skip_special_tokens": True,
            }
            for k, v in defaults.items():
                filtered_kwargs.setdefault(k, v)

            response = self.generate_response(
                conversation_text,
                add_system_prompt=False,  # Already in conversation
                include_prompt=False,
                **filtered_kwargs
            )

            # Save raw response for debugging
            try:
                repo_root = Path(__file__).resolve().parents[2]
                dbg_dir = repo_root / "debug_prompts"
                raw_file = dbg_dir / f"{problem_base}_raw_response_iter{iteration+1}.txt"
                raw_file.write_text(response, encoding="utf-8")
            except Exception as e:
                print(f"[DEBUG] Failed to write raw response log: {e}")
                pass
            
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

            # Plan is invalid, provide structured feedback using either the provided
            # domain-specific feedback function or the generic validation prompt.
            error_msg = validation_result.get("error", "Plan validation failed")

            if validation_feedback_fn is not None:
                try:
                    feedback = validation_feedback_fn(initial_prompt, plan_text, error_msg)
                except Exception:
                    feedback = f"The plan is invalid. Error: {error_msg}. Please provide a corrected plan."
            else:
                try:
                    from ..prompts.prompts import validation_feedback_prompt

                    feedback = validation_feedback_prompt(initial_prompt, plan_text, error_msg)
                except Exception:
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