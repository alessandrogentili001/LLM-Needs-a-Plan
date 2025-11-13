#!/usr/bin/env python3
"""
Main entry point for the PDDL Planning Framework with Large Language Models.

This script provides the command-line interface for the LLM-Needs-a-Plan system,
allowing users to run planning experiments with different models and domains.
"""

# Standard library imports
import os
import sys
import argparse
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# Import core modules
from core.pddl_planner import PDDLPlanner   # Comes with other core modules FileManager, ModelManager, PDDLProcessor
from utils.configuration import load_config # config.yml file loader


def main():
    """Main function to run the PDDL planning pipeline."""
    
    print("Starting PDDL Planning Framework...")
    print("=" * 50)
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="PDDL Planning with Large Language Models",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Path arguments: Problems, Models, Outputs
    parser.add_argument(
        "--problems_path",
        default=config.get("PROBLEMS_PATH", "src/data"),       # Problems path 
        help="Path to PDDL problem files directory"
    )
    parser.add_argument(
        "--weights_path", 
        default=config.get("MODEL_PATH", "src/models"),        # Model weights path
        help="Path to model weights directory"
    )
    parser.add_argument(
        "--output_dir",
        default=config.get("MODEL_OUTPUT", "src/results"),
        help="Directory to save generated plans and outputs"   # Output directory
    )
    
    # Processing options: Batch, Domain, Iterations
    parser.add_argument(
        "--batch",
        action="store_true",                                    
        default=False,                                         # Process all domains   
        help="Process all domains in batch mode"
    )
    parser.add_argument(
        "--domain",
        type=str,                                              # Specific domain to process
        help="Process only the specified domain"
    )
    parser.add_argument(
        "--max_iterations",
        type=int,                                              # Max validation iterations per problem
        default=1,
        help="Maximum validation iterations per problem"
    )
    
    # Model generation options: Sampling, Temperature, Max Tokens
    parser.add_argument(
        "--sampling",
        action="store_true", 
        default=False,
        help="Use sampling for generation (temperature 0.6, top_k 10)" 
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Temperature for sampling (only used with --sampling)"
    )
    parser.add_argument(
        "--max_tokens",
        type=int,
        default=1024,
        help="Maximum tokens to generate per response"
    )
    
    # Prompt options: System prompt, CoT
    parser.add_argument(
        "--add_system_prompt",
        action="store_true",
        default=True,
        help="Add system prompt to model input"
    )
    parser.add_argument(
        "--cot", 
        action="store_true",
        default=True,
        help="Enable Chain of Thought prompting"
    )
    
    # Output options: Include prompt, Skip special tokens
    parser.add_argument(
        "--include_prompt",
        action="store_true",
        default=True,
        help="Include the prompt in the output files"
    )
    parser.add_argument(
        "--skip_special_tokens",
        action="store_true",
        default=True,
        help="Skip special tokens in the output"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Enable verbose output"
    )
    
    # Model selection
    parser.add_argument(
        "--model",
        choices=["llama3", "phi4", "gemma3", "kimi", "auto"],
        default="auto",
        help="Model type to use (auto-detect from path if 'auto')"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.verbose:
        print("Parsed arguments:")
        for arg, value in vars(args).items():
            print(f"  {arg}: {value}")
        print()
    
    # Validate paths
    if not Path(args.problems_path).exists():
        print(f"Error: Problems path does not exist: {args.problems_path}")
        sys.exit(1)
    
    if not Path(args.weights_path).exists():
        print(f"Error: Model weights path does not exist: {args.weights_path}")
        sys.exit(1)
    
    try:
        # Initialize and run planner
        planner = PDDLPlanner(args, config)
        planner.setup() # Load models (ModelManager) and problems (FileManager)
        planner.run()   # Run the planning process (PDDLProcessor)
        
        print("\nPDDL Planning Framework completed successfully!")
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during execution: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()