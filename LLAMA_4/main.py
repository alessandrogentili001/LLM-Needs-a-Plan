import os
import sys
from pddl_processor import PDDLProcessor  # PDDLProcessor class to handle structured PDDL processing
from file_manager import FileManager      # FileManager class to handle file operations and structure PPDL files
import argparse                           # For command line argument parsing

# Add parent directory to path to access utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.configuration import CONFIG    # Load configuration settings


class PDDLPlanner:
    """Main class for the PDDL Planning application."""

    def __init__(self, args):
        """Initialize the PDDLPlanner with parsed arguments."""
        self.args = args               # args passed from main                  --> parsed command line arguments
        self.file_mng = FileManager()  # file manager to handle PDDL files      --> find PDDL files in the specified directory
        self.model_manager = None      # model manager initialized with setup() --> load the model
        self.processor = None          # processor initialized with setup()     --> process the PDDL files

    def setup(self):
        """Set up the planner by loading the model, processor and creating directories."""

        # choose the right Class ModelManager() based on the model path provided in args
        if "Phi4" in self.args.weights_path:
            from model_manager_phi4 import ModelManager
        else:
            from model_manager import ModelManager

        # Initialize the manager 
        self.model_manager = ModelManager(self.args.weights_path)

        # Load the model
        self.model_manager.load()

        # Ensure output directory exists
        os.makedirs(self.args.output_dir, exist_ok=True)

        # Initialize processor with model manager and output directory
        self.processor = PDDLProcessor(self.model_manager, self.args.output_dir)

    def run(self):
        """Run the PDDL planning process."""

        # Load args
        args = self.args

        # Load file manager 
        file_manager = self.file_mng

        # Load processor 
        processor = self.processor

        # Find PDDL files in the specified problems path
        pddl_data_info = file_manager.find_pddl_files(problems_path=args.problems_path)
        """
        ***Example structure of pddl_data_info***

        pddl_data_info = [
            {
                "domain_path": "/datasets/logistics/domain.pddl",
                "domain_text": "(define (domain logistics) ...)",
                "domain_name": "logistics", 
                "problem_paths": [
                    "/datasets/logistics/prob01.pddl",
                    "/datasets/logistics/prob02.pddl",
                    ...
                ]
            },
            {
                "domain_path": "/datasets/blocksworld/domain.pddl", 
                "domain_text": "(define (domain blocks) ...)",
                "domain_name": "blocksworld",
                "problem_paths": [
                    "/datasets/blocksworld/prob01.pddl",
                    "/datasets/blocksworld/prob02.pddl", 
                    ...
                ]
            }, 
            ...
        ]
        """

        # Check if any PDDL files were found
        if not pddl_data_info:
            print("\nNo valid PDDL domains found")
            return

        # Process each domain
        for domain_data in pddl_data_info:  # iterate over the domains with associated problems
            processor.process_with_validation(domain_data, args)

        print("\nProcessing complete!")


def main():
    """Main function to run the program."""
    parser = argparse.ArgumentParser(description="PDDL Planning with LLMs")

    parser.add_argument(
        "--problems_path",
        default=CONFIG["PROBLEMS_PATH"],
        help="Path to PDDL problem files",
    )
    parser.add_argument(
        "--weights_path",
        default=CONFIG["MODEL_PATH"],
        help="Path to model weights",
    )
    parser.add_argument(
        "--output_dir",
        default=CONFIG["MODEL_OUTPUT"],
        help="Directory to save outputs (defaults to ./model_outputs)",
    )
    parser.add_argument(
        "--batch",
        default=False,
        action="store_true",
        help="Process problems in batch mode",
    )
    parser.add_argument(
        "--include_prompt",
        default=True,
        action="store_true",
        help="Include the prompt in the output",
    )
    parser.add_argument(
        "--skip_special_tokens",
        default=False,
        action="store_true",
        help="Skip special tokens in the output",
    )
    parser.add_argument(
        "--cot",
        default=False,
        action="store_true",
        help="Use Chain of Thought (CoT) prompting",
    )
    parser.add_argument(
        "--sampling",
        default=False,
        action="store_true",
        help="Use sampling for generation (temperature 0.6, otherwise 0.0). Top_k: 10 for sampling",
    )
    parser.add_argument(
        "--add_system_prompt",
        action="store_true",
        default=True,
        help="Add system prompt to the input",
    )
    parser.add_argument(
        "--planner_validator",
        default=True,
        action="store_true",
        help="Use planner-validator framework. With planner-validator batch cannot be used.",
    )

    # Parsing arguments from command line
    print("\nParsing command line arguments...")
    args = parser.parse_args()
    print(f"\nArguments: {args}")
    
    # Initialize the planner 
    planner = PDDLPlanner(args)

    # Setup the planner 
    print("\nSetting up PDDL Planner with the following configuration:")
    planner.setup()

    # Run the planner
    print("\nPDDL Planner setup complete. Starting processing...")
    planner.run()


if __name__ == "__main__":
    print("\nStarting PDDL Planning Framework...")
    main()
