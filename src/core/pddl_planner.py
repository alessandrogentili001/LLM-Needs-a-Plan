"""
PDDL Planner - Main Orchestrator

Main orchestrator class for the PDDL Planning Framework.
Coordinates all components including FileManager, ModelManager, and PDDLProcessor
to provide a complete planning solution.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import core modules with proper error handling
try:
    from .file_manager import FileManager
    from .model_manager import ModelManager
    from .pddl_processor import PDDLProcessor
    from ..utils.configuration import load_config
except ImportError:
    # Fallback imports for when run directly
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.core.file_manager import FileManager
    from src.core.model_manager import ModelManager
    from src.core.pddl_processor import PDDLProcessor
    from src.utils.configuration import load_config


class PDDLPlanner:
    """
    Main orchestrator for the PDDL Planning Framework.
    
    Coordinates the complete planning pipeline:
    - File discovery and organization
    - Model loading and management
    - PDDL processing and plan generation
    - Output management and reporting
    """

    def __init__(self, args, config: Optional[Dict] = None):
        """
        Initialize the PDDLPlanner with command line arguments.

        Args:
            args: Parsed command line arguments
            config (Optional[Dict]): Configuration dictionary (loaded if not provided)
        """
        self.args = args
        self.config = config or load_config()
        
        # Core components (initialized in setup())
        self.file_manager = None
        self.model_manager = None
        self.processor = None
        
        # Processing state
        self.domains_data = None
        self.results = {}
        
        print(f"PDDLPlanner initialized")
        print(f"  Problems path: {args.problems_path}")
        print(f"  Model path: {args.weights_path}")
        print(f"  Output directory: {args.output_dir}")

    def setup(self):
        """Set up all components required for planning."""
        
        print("\nSetting up PDDL Planner components...")
        
        # Initialize file manager
        print("  Initializing FileManager...")
        self.file_manager = FileManager()
        
        # Discover PDDL domains and problems
        print(f"  Discovering PDDL files in: {self.args.problems_path}")
        self.domains_data = self.file_manager.find_pddl_files(self.args.problems_path)
        
        if not self.domains_data:
            raise ValueError(f"No PDDL domains found in {self.args.problems_path}")
        
        print(f"  Found {len(self.domains_data)} domain(s):")
        for domain_data in self.domains_data:
            domain_name = domain_data["domain_name"]
            problem_count = len(domain_data["problem_paths"])
            print(f"    - {domain_name}: {problem_count} problems")
        
        # Filter domains if specific domain requested
        if self.args.domain:
            print(f"  Filtering for domain: {self.args.domain}")
            self.domains_data = [
                d for d in self.domains_data 
                if d["domain_name"].lower() == self.args.domain.lower()
            ]
            
            if not self.domains_data:
                raise ValueError(f"Domain '{self.args.domain}' not found")
        
        # Initialize model manager
        print("  Initializing ModelManager...")
        model_path = self._resolve_model_path()
        self.model_manager = ModelManager(model_path)
        
        print("  Loading model (this may take a while)...")
        try:
            self.model_manager.load()
            model_info = self.model_manager.get_model_info()
            print(f"  Model loaded successfully: {model_info.get('model_type', 'unknown')}")
            print(f"  Parameters: {model_info.get('parameters', 'unknown')}")
            print(f"  Device: {model_info.get('device', 'unknown')}")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")
        
        # Initialize processor
        print("  Initializing PDDLProcessor...")
        self.processor = PDDLProcessor(
            model_manager=self.model_manager,
            output_dir=self.args.output_dir
        )
        
        print("PDDL Planner setup complete!")

    def run(self):
        """Run the PDDL planning process."""
        
        print("\nStarting PDDL planning process...")
        print("=" * 50)
        
        if not self.domains_data:
            raise RuntimeError("No domains available. Run setup() first.")
        
        # Prepare processing arguments
        processing_kwargs = {
            "max_iterations": self.args.max_iterations,
            "enable_cot": self.args.cot,
            "add_system_prompt": self.args.add_system_prompt,
            "sampling": self.args.sampling,
            "max_tokens": self.args.max_tokens,
            "temperature": self.args.temperature,
            "include_prompt": self.args.include_prompt,
            "skip_special_tokens": self.args.skip_special_tokens
        }
        
        if self.args.batch:
            # Process all domains in batch
            print("Running batch processing for all domains...")
            self.results = self.processor.batch_process_domains(
                domains_data=self.domains_data,
                **processing_kwargs
            )
        else:
            # Process domains individually
            self.results = {
                "domain_results": [],
                "overall_stats": {
                    "total_problems": 0,
                    "total_successful": 0,
                    "total_failed": 0
                }
            }
            
            for i, domain_data in enumerate(self.domains_data, 1):
                print(f"\nProcessing domain {i}/{len(self.domains_data)}: {domain_data['domain_name']}")
                print("-" * 40)
                
                try:
                    domain_result = self.processor.process_domain_with_validation(
                        domain_data=domain_data,
                        **processing_kwargs
                    )
                    
                    self.results["domain_results"].append(domain_result)
                    
                    # Update overall statistics
                    stats = self.results["overall_stats"]
                    stats["total_problems"] += domain_result["total_problems"]
                    stats["total_successful"] += domain_result["successful_plans"]
                    stats["total_failed"] += domain_result["failed_plans"]
                    
                except Exception as e:
                    print(f"Error processing domain {domain_data['domain_name']}: {e}")
                    self.results["domain_results"].append({
                        "domain_name": domain_data["domain_name"],
                        "error": str(e),
                        "total_problems": len(domain_data.get("problem_paths", [])),
                        "successful_plans": 0,
                        "failed_plans": len(domain_data.get("problem_paths", []))
                    })
        
        # Print final summary
        self._print_final_summary()

    def _resolve_model_path(self) -> str:
        """
        Resolve the full model path based on arguments and model type.

        Returns:
            str: Full path to the model directory
        """
        weights_path = Path(self.args.weights_path)
        
        # If path points to a specific model directory, use it directly
        if (weights_path / "config.json").exists():
            return str(weights_path)
        
        # If path is a models directory, try to find the right model
        if weights_path.is_dir():
            model_dirs = [d for d in weights_path.iterdir() if d.is_dir()]
            
            # If specific model type requested
            if self.args.model != "auto":
                target_model = self.args.model.lower()
                for model_dir in model_dirs:
                    if target_model in model_dir.name.lower():
                        if (model_dir / "config.json").exists():
                            print(f"  Selected model: {model_dir.name}")
                            return str(model_dir)
            
            # Auto-select first available model
            for model_dir in model_dirs:
                if (model_dir / "config.json").exists():
                    print(f"  Auto-selected model: {model_dir.name}")
                    return str(model_dir)
        
        # Fallback to original path
        return str(weights_path)

    def _print_final_summary(self):
        """Print final processing summary."""
        
        print(f"\n" + "=" * 60)
        print("FINAL PROCESSING SUMMARY")
        print("=" * 60)
        
        if "overall_stats" in self.results:
            stats = self.results["overall_stats"]
            total_problems = stats["total_problems"]
            successful = stats["total_successful"]
            failed = stats["total_failed"]
            
            success_rate = (successful / total_problems) * 100 if total_problems > 0 else 0
            
            print(f"Domains processed: {len(self.results['domain_results'])}")
            print(f"Total problems: {total_problems}")
            print(f"Successful plans: {successful}")
            print(f"Failed plans: {failed}")
            print(f"Success rate: {success_rate:.1f}%")
            
            # Domain-by-domain breakdown
            print(f"\nDomain Breakdown:")
            for domain_result in self.results["domain_results"]:
                domain_name = domain_result["domain_name"]
                if "error" in domain_result:
                    print(f"  {domain_name}: ERROR - {domain_result['error']}")
                else:
                    domain_success = domain_result["successful_plans"]
                    domain_total = domain_result["total_problems"]
                    domain_rate = (domain_success / domain_total) * 100 if domain_total > 0 else 0
                    print(f"  {domain_name}: {domain_success}/{domain_total} ({domain_rate:.1f}%)")
        
        print(f"\nOutput directory: {self.args.output_dir}")
        print("=" * 60)

    def get_results(self) -> Dict[str, Any]:
        """
        Get processing results.

        Returns:
            Dict[str, Any]: Complete results from processing
        """
        return self.results

    def get_planner_info(self) -> Dict[str, Any]:
        """
        Get information about the planner configuration.

        Returns:
            Dict[str, Any]: Planner configuration information
        """
        return {
            "arguments": vars(self.args),
            "config": self.config,
            "domains_available": len(self.domains_data) if self.domains_data else 0,
            "model_info": self.model_manager.get_model_info() if self.model_manager else None,
            "processor_info": self.processor.get_processor_info() if self.processor else None
        }