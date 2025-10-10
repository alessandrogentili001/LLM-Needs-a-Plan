import os
from pathlib import Path


class FileManager:
    """Manages file operations for PDDL files and generated plans.
    find_pddl_files: for each domain file, associates a list of problem file paths with it
    """

    def __init__(self):
        """Initialize the FileManager."""
        pass

    def read_file(self, file_path):
        """Read a file and return its contents.

        Args:
            file_path (str): Path to the file

        Returns:
            str: Contents of the file or None if error
        """

        # Ensure directory exists
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None

        # Open and read the file content
        try:
            with open(file_path, "r") as f:
                return f.read()  # Return file content in STRING format 
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def save_file(self, output_file_path, content):
        """Save content to a file.

        Args:
            output_file_path (str): Path to save the file
            content (str): Content to save

        Returns:
            bool: True if successful, False otherwise
        """

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        try:
            # Write content to file
            with open(output_file_path, "w") as f:
                f.write(content)
            print(f"Saved plan to {output_file_path}")
            return True
        except Exception as e:
            print(f"Error saving file {output_file_path}: {e}")
            return False

    def find_pddl_files(self, data_path):
        """Find all domain and problem files in the given directory.

        Args:
            data_path (str): Path to search for PDDL files

        Returns:
            list: List of dictionaries containing domain and problem file information
        """

        # Initialize the list to hold domain and problem file info
        pddl_directories = []

        # Walk through the directory to find PDDL files
        for root, _, files in os.walk(data_path):

            # Find domain files in current directory
            domain_files = [f for f in files if f.endswith("_domain.pddl")]
            if not domain_files:
                print(f"No domain files found in {root}")
                continue

            # Join the domain file path and read its content
            domain_path = os.path.join(root, domain_files[0])  # usually only one domain file
            domain_text = self.read_file(domain_path)
            if domain_text is None:
                print(f"Skipping domain file {domain_path} due to read error")
                continue

            # Find problem files in current directory
            problem_paths = [os.path.join(root, f) for f in files if f.endswith(".pddl") and not f.endswith("_domain.pddl")]  # all files other than domain
            if not problem_paths:
                print(f"No problem files found in {root}")
                continue

            # Extract domain name from the domain file name
            domain_name = Path(domain_files[0]).stem.split("_domain")[0]

            # Append the domain and its associated problems to the list
            pddl_directories.append(
                {  
                    "domain_path": domain_path,
                    "domain_text": domain_text,
                    "domain_name": domain_name,
                    "problem_paths": problem_paths,  # list of all problem files for this domain
                }
            )

        return pddl_directories
