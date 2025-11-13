"""
PDDL Processor for LLM Planning

Processes PDDL planning problems and orchestrates plan generation using large language models.
Handles domain-problem pairs, prompt creation, and plan validation workflows.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import utilities with proper error handling
try:
    from ..utils.validator import validate_plan_from_text
    from ..utils.answer_postprocessor import formatter
    from .file_manager import FileManager
    from .model_manager import ModelManager
    from ..prompts.prompts import (
            system_prompt_pddl,
            tetris_problem_prompt,
            generic_pddl_prompt,
            chain_of_thought_prompt,
            citycar_problem_prompt,
            add_examples_to_prompt,
            add_constraints_to_prompt,
            validation_feedback_prompt
    )
except ImportError:
    # Fallback imports for when run directly
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.utils.validator import validate_plan_from_text
    from src.utils.answer_postprocessor import formatter
    from src.core.file_manager import FileManager
    from src.core.model_manager import ModelManager
    from src.prompts.prompts import (
        system_prompt_pddl,
        tetris_problem_prompt,
        generic_pddl_prompt,
        chain_of_thought_prompt,
        citycar_problem_prompt,
        validation_feedback_prompt,
        add_examples_to_prompt,
        add_constraints_to_prompt
    )


class PDDLProcessor:
    """
    Processes PDDL planning problems using large language models.
    
    Orchestrates the complete planning pipeline:
    - Domain and problem file processing
    - Prompt generation for different domains
    - LLM-based plan generation
    - Plan validation and iterative refinement
    - Output management and saving
    """

    def __init__(self, model_manager: ModelManager, output_dir: str):
        """
        Initialize the PDDLProcessor.

        Args:
            model_manager (ModelManager): Loaded model manager instance
            output_dir (str): Directory to save generated plans and outputs
        """
        self.model_manager = model_manager
        self.output_dir = Path(output_dir)
        self.file_manager = FileManager()
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"PDDLProcessor initialized with output directory: {self.output_dir}")

    def process_domain_with_validation(
        self,
        domain_data: Dict[str, Any],
        max_iterations: int = 3,
        enable_cot: bool = False,
        add_system_prompt: bool = True,
        sampling: bool = False,
        **generation_kwargs
    ) -> Dict[str, Any]:
        """
        Process all problems in a domain with plan validation.

        Args:
            domain_data (Dict): Domain information from FileManager
            max_iterations (int): Maximum validation iterations per problem
            enable_cot (bool): Enable Chain of Thought prompting
            add_system_prompt (bool): Add system prompt to generation
            sampling (bool): Use sampling for generation
            **generation_kwargs: Additional arguments for generation

        Returns:
            Dict[str, Any]: Processing results including success rates and outputs
        """
        # Extract domain information
        domain_name = domain_data["domain_name"]
        domain_text = domain_data["domain_text"]
        domain_path = domain_data["domain_path"]
        problem_paths = domain_data["problem_paths"]
        
        print(f"Processing domain: {domain_name}")
        print(f"Domain file: {domain_path}")
        print(f"Problems to process: {len(problem_paths)}")
        
        # Create domain-specific output directory
        domain_output_dir = self.output_dir / domain_name
        domain_output_dir.mkdir(exist_ok=True)
        
        # Track processing results
        results = {
            "domain_name": domain_name,
            "total_problems": len(problem_paths),
            "successful_plans": 0,
            "failed_plans": 0,
            "problem_results": [],
            "output_directory": str(domain_output_dir)
        }
        
        # Process each problem instance
        for i, problem_path in enumerate(problem_paths, 1):
            print(f"\n[{i}/{len(problem_paths)}] Processing: {Path(problem_path).name}")
            
            try:
                problem_result = self._process_single_problem(
                    domain_name=domain_name,
                    domain_text=domain_text,
                    domain_path=domain_path,
                    problem_path=problem_path,
                    output_dir=domain_output_dir,
                    max_iterations=max_iterations,
                    enable_cot=enable_cot,
                    add_system_prompt=add_system_prompt,
                    sampling=sampling,
                    **generation_kwargs
                )
                
                results["problem_results"].append(problem_result)
                
                if problem_result["plan_valid"]:
                    results["successful_plans"] += 1
                    print(f"  Valid plan generated in {problem_result['iterations']} iterations")
                else:
                    results["failed_plans"] += 1
                    print(f"  Failed to generate valid plan after {problem_result['iterations']} iterations")
                    
            except Exception as e:
                print(f"  Error processing problem: {e}")
                results["failed_plans"] += 1
                results["problem_results"].append({
                    "problem_path": problem_path,
                    "problem_name": Path(problem_path).stem,
                    "plan_valid": False,
                    "iterations": 0,
                    "error": str(e)
                })
        
        # Print summary
        success_rate = (results["successful_plans"] / results["total_problems"]) * 100
        print(f"\nDomain '{domain_name}' processing complete:")
        print(f"  Success rate: {success_rate:.1f}% ({results['successful_plans']}/{results['total_problems']})")
        print(f"  Output directory: {domain_output_dir}")
        
        return results

    def _process_single_problem(
        self,
        domain_name: str,
        domain_text: str,
        domain_path: str,
        problem_path: str,
        output_dir: Path,
        max_iterations: int = 3,
        enable_cot: bool = False,
        add_system_prompt: bool = True,
        sampling: bool = False,
        **generation_kwargs
    ) -> Dict[str, Any]:
        """
        Process a single problem instance.

        Args:
            domain_name (str): Name of the domain
            domain_text (str): Domain PDDL content
            domain_path (str): Path to domain file
            problem_path (str): Path to problem file
            output_dir (Path): Output directory for this domain
            max_iterations (int): Maximum validation iterations
            enable_cot (bool): Enable Chain of Thought prompting
            add_system_prompt (bool): Add system prompt
            sampling (bool): Use sampling for generation
            **generation_kwargs: Additional generation arguments

        Returns:
            Dict[str, Any]: Processing result for this problem
        """
        problem_name = Path(problem_path).stem
        
        # Read problem file
        problem_text = self.file_manager.read_file(problem_path)
        if problem_text is None:
            raise ValueError(f"Failed to read problem file: {problem_path}")
        
        # Build an optimized, domain-specific prompt using the internal pipeline
        prompt_text = self._build_prompt(
            domain_name=domain_name,
            domain_text=domain_text,
            problem_text=problem_text,
            enable_cot=enable_cot
        )

        # --- DEBUG: print the exact prompt we will send to the model so cluster
        # jobs capture it in stdout/stderr logs (easier to inspect than files).
        try:
            print(f"\n---PROMPT SENT TO MODEL for {problem_name}---\n{prompt_text}\n---END PROMPT---\n")
        except Exception:
            # non-fatal if printing fails
            pass

        # Select domain-specific validation feedback function when available
        validation_feedback_fn = self._get_validation_feedback_fn(domain_name)

        # Generate plan with validation. generation_kwargs already forwarded from caller
        response_text, iterations, is_valid = self.model_manager.iterative_planning_with_validation(
            domain_path=domain_path,
            problem_path=problem_path,
            initial_prompt=prompt_text,
            max_iterations=max_iterations,
            add_system_prompt=add_system_prompt,
            validation_feedback_fn=validation_feedback_fn,
            sampling=sampling,
            **generation_kwargs
        )
        
        # Add processing metadata to response
        metadata = f"\n\n--- Processing Metadata ---\n"
        metadata += f"Domain: {domain_name}\n"
        metadata += f"Problem: {problem_name}\n"
        metadata += f"Iterations: {iterations}\n"
        metadata += f"Plan Valid: {is_valid}\n"
        metadata += f"Chain of Thought: {enable_cot}\n"
        
        final_response = response_text + metadata
        
        # Save the generated plan
        plan_filename = f"{problem_name}_plan.txt"
        plan_path = output_dir / plan_filename
        
        self.file_manager.save_file(str(plan_path), final_response)
        
        return {
            "problem_path": problem_path,
            "problem_name": problem_name,
            "plan_path": str(plan_path),
            "plan_valid": is_valid,
            "iterations": iterations,
            "response_length": len(response_text),
            "cot_enabled": enable_cot
        }

    def _create_domain_prompt(self, domain_name: str, domain_text: str, problem_text: str, include_examples: bool = True) -> str:
        """
        Create appropriate prompt based on domain type.

        Args:
            domain_name (str): Name of the domain
            domain_text (str): Domain PDDL content
            problem_text (str): Problem PDDL content

        Returns:
            str: Formatted prompt for the domain
        """
        # Keep legacy domain prompt selection but prefer explicit domain-specific functions
        domain_lower = domain_name.lower()

        # Prefer domain-specific builders but allow caller to decide whether the
        # domain builder should include few-shot examples (we often add examples
        # later in a centralized place to avoid duplication).
        if "tetris" in domain_lower:
            print(f"Using Tetris prompt for domain: {domain_name}")
            return tetris_problem_prompt(domain_text, problem_text, include_examples=include_examples)
        if "citycar" in domain_lower:
            print(f"Using CityCar prompt for domain: {domain_name}")
            return citycar_problem_prompt(domain_text, problem_text, include_examples=include_examples)

        # Default to generic prompt
        print(f"Using generic PDDL prompt for domain: {domain_name}")
        return generic_pddl_prompt(domain_text, problem_text)

    def _build_prompt(
        self,
        domain_name: str,
        domain_text: str,
        problem_text: str,
        enable_cot: bool = False,
        examples: Optional[List[str]] = None,    # few-shot examples
        constraints: Optional[List[str]] = None, # additional constraints
    ) -> str:
        """
        Build a consolidated prompt for the planner.

        Returns a string suitable to pass as the initial user prompt to the model manager.
        The pipeline selects a domain-specific base prompt, optionally appends CoT instructions,
        example plan(s), and additional constraints.
        """
        # Truncate domain/problem texts to a safe length before building prompts.
        domain_safe = domain_text # self._safely_truncate_text(domain_text)
        problem_safe = problem_text # self._safely_truncate_text(problem_text)

        # Build base prompt using domain-specific builder but avoid allowing it to
        # inject examples on its own; we add examples in a central place below to
        # avoid duplication and keep the pipeline predictable.
        # Prepend a short, high-priority instruction that must always be seen by
        # the model. This protects against truncation removing essential output
        # constraints and prevents the model from asking for missing input.
        top_instruction = (
            "OUTPUT ONLY: Provide the final PDDL action sequence, one action per line. "
            "Do NOT ask clarifying questions or request additional information — use the DOMAIN and PROBLEM definitions provided."
        )

        base = self._create_domain_prompt(domain_name, domain_safe, problem_safe, include_examples=False)
        base = top_instruction + "\n\n" + base

        # Examples: prefer explicit `examples` passed by caller; otherwise try to
        # load canonical few-shot examples for the domain (lazy).
        if not examples:
            examples = self._load_domain_examples(domain_name)

        if examples:
            try:
                from ..prompts.prompts import add_examples_to_prompt

                base = add_examples_to_prompt(base, examples)
            except Exception:
                base += "\n\n" + "\n\n".join(examples)

        # Add custom constraints if provided
        if constraints:
            try:
                base = add_constraints_to_prompt(base, constraints)
            except Exception:
                base += "\n\nAdditional constraints:\n" + "\n".join(constraints)
        else:
            pass # no constraints to add

        # Add chain-of-thought instructions if requested (append after plan-only to keep separation)
        if enable_cot:
            try:
                # Prefer domain-specific CoT wrappers when available
                dn = domain_name.lower()
                if "tetris" in dn:
                    from ..prompts.prompts import tetris_chain_of_thought as _cot_fn
                elif "citycar" in dn:
                    from ..prompts.prompts import citycar_chain_of_thought as _cot_fn
                else:
                    from ..prompts.prompts import chain_of_thought_prompt as _cot_fn

                cot_text = _cot_fn(domain_safe, problem_safe) # Load domain-specific CoT if available
                base = base + "\n\n" + cot_text               # Add CoT instructions to the base prompt
            except Exception:
                base = base + "\n\n" + "Please think step by step about the plan, then output only the final action sequence."

        return base

    def _safely_truncate_text(self, text: str, max_chars: int = 4000) -> str:
        """
        Truncate long domain/problem texts to a safe character length. This is a
        light-weight guard against exceeding tokenizer/model input limits. It
        prefers to keep the head and tail of the text where possible.
        """
        if not text:
            return ""
        if len(text) <= max_chars:
            return text

        head = text[: max_chars // 2]
        tail = text[- (max_chars // 2) :]
        return head + "\n\n...TRUNCATED...\n\n" + tail

    def _load_domain_examples(self, domain_name: str) -> Optional[List[str]]:
        """
        Try to lazy-load domain few-shot examples from `src.prompts.prompts`.
        Returns None if examples are not available.
        """
        try:
            from ..prompts import prompts as _prompts_mod

            dn = domain_name.lower()
            if "tetris" in dn and hasattr(_prompts_mod, '_format_tetris_examples'):
                return _prompts_mod._format_tetris_examples()
            if "citycar" in dn and hasattr(_prompts_mod, '_format_citycar_examples'):
                return _prompts_mod._format_citycar_examples()
        except Exception:
            return None

        return None

    def _get_validation_feedback_fn(self, domain_name: str):
        """
        Return a domain-specific validation feedback function when available.
        """
        dn = domain_name.lower()
        if "tetris" in dn:
            try:
                from ..prompts.prompts import tetris_validation_feedback

                return tetris_validation_feedback
            except Exception:
                return None
        if "citycar" in dn:
            try:
                from ..prompts.prompts import citycar_validation_feedback

                return citycar_validation_feedback
            except Exception:
                return None

        return None

    def batch_process_domains(
        self,
        domains_data: List[Dict[str, Any]],
        max_iterations: int = 3,
        enable_cot: bool = False,
        **processing_kwargs
    ) -> Dict[str, Any]:
        """
        Process multiple domains in batch.

        Args:
            domains_data (List[Dict]): List of domain data from FileManager
            max_iterations (int): Maximum validation iterations per problem
            enable_cot (bool): Enable Chain of Thought prompting
            **processing_kwargs: Additional processing arguments

        Returns:
            Dict[str, Any]: Batch processing results
        """
        print(f"Starting batch processing of {len(domains_data)} domains")
        
        batch_results = {
            "total_domains": len(domains_data),
            "domain_results": [],
            "overall_stats": {
                "total_problems": 0,
                "total_successful": 0,
                "total_failed": 0
            }
        }
        
        for i, domain_data in enumerate(domains_data, 1):
            print(f"\n{'='*50}")
            print(f"Domain {i}/{len(domains_data)}")
            print(f"{'='*50}")
            
            try:
                domain_result = self.process_domain_with_validation(
                    domain_data=domain_data,
                    max_iterations=max_iterations,
                    enable_cot=enable_cot,
                    **processing_kwargs
                )
                
                batch_results["domain_results"].append(domain_result)
                
                # Update overall statistics
                batch_results["overall_stats"]["total_problems"] += domain_result["total_problems"]
                batch_results["overall_stats"]["total_successful"] += domain_result["successful_plans"]
                batch_results["overall_stats"]["total_failed"] += domain_result["failed_plans"]
                
            except Exception as e:
                print(f"Error processing domain {domain_data.get('domain_name', 'unknown')}: {e}")
                batch_results["domain_results"].append({
                    "domain_name": domain_data.get("domain_name", "unknown"),
                    "error": str(e),
                    "total_problems": len(domain_data.get("problem_paths", [])),
                    "successful_plans": 0,
                    "failed_plans": len(domain_data.get("problem_paths", []))
                })
        
        # Print overall summary
        stats = batch_results["overall_stats"]
        overall_success_rate = (stats["total_successful"] / stats["total_problems"]) * 100 if stats["total_problems"] > 0 else 0
        
        print(f"\n{'='*50}")
        print(f"BATCH PROCESSING COMPLETE")
        print(f"{'='*50}")
        print(f"Domains processed: {batch_results['total_domains']}")
        print(f"Total problems: {stats['total_problems']}")
        print(f"Overall success rate: {overall_success_rate:.1f}% ({stats['total_successful']}/{stats['total_problems']})")
        print(f"Output directory: {self.output_dir}")
        
        return batch_results

    def get_processor_info(self) -> Dict[str, Any]:
        """
        Get information about the processor configuration.

        Returns:
            Dict[str, Any]: Processor information
        """
        return {
            "output_directory": str(self.output_dir),
            "model_info": self.model_manager.get_model_info() if self.model_manager else None,
            "file_manager_available": self.file_manager is not None
        }