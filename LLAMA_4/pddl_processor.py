import os
import prompts
from file_manager import FileManager
from pathlib import Path


class PDDLProcessor:
    """Processes PDDL problems and generates plans using language models.
    Uses prompts.py to create prompts for the model. Eg: ppdl_problem_prompt, cot_prompt
    """

    def __init__(self, model_manager, output_dir):
        """Initialize the PDDLProcessor.

        Args:
            model_manager (ModelManager): ModelManager instance
            output_dir (str): Directory to save outputs
        """
        self.model_manager = model_manager              # ModelManager instance
        self.output_dir = output_dir                    # Output directory for plans  
        self.file_manager = file_manager.FileManager()  # FileManager instance

    def process_with_validation(self, domain_data, args):
        """Process each problem in a domain with validation of the plan.

        Args:
            domain_data (dict): Dictionary containing domain information
            args: Command line arguments
        """

        # Extract data info 
        domain_text = domain_data["domain_text"]      # domain file content in STRING format
        problem_paths = domain_data["problem_paths"]  # list of all problem files for this domain
        domain_name = domain_data["domain_name"]      # domain name extracted from domain file path

        # Create output directory for this domain
        domain_output_dir = os.path.join(self.output_dir, domain_name)  # create domain-specific output directory
        os.makedirs(domain_output_dir, exist_ok=True)                   # create the directory if it doesn't exist
        domain_data["domain_output_dir"] = domain_output_dir            # add output dir to domain data for reference

        # Process each problem instance individually
        for problem_path in problem_paths:

            # read the file and check for errors
            problem_text = self.file_manager.read_file(problem_path)
            if problem_text is None:
                continue

            print(f"\nGenerating plan for {problem_path}...")

            # Uses the domain text and problem text to create the prompt
            problem_prompt = prompts.tetris_problem_prompt(domain_text, problem_text)

            # Enable chain of thoughts if needed
            if args.cot:
                problem_prompt = prompts.cot_prompt(problem_prompt)                

            # Generate the plan with validation (multiple iterations if needed)
            response_text, iterations = self.model_manager.generate_with_validation(
                problem_prompt,
                problem_path,
                domain_data,
                max_tokens=5000,
                add_system_prompt=args.add_system_prompt,
                sampling=args.sampling,
                include_prompt=args.include_prompt,
                skip_special_tokens=args.skip_special_tokens,
            )

            # Add info for readability 
            response_text = (
                response_text + "\n\n" + f"Generated in {iterations} iterations."
            )

            # Save the generated plan
            problem_name = Path(problem_path).stem
            plan_path = os.path.join(domain_output_dir, f"{problem_name}_plan.txt")
            self.file_manager.save_file(plan_path, response_text)
