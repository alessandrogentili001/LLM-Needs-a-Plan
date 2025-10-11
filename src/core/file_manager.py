"""
File Manager for PDDL Planning

Manages file operations for PDDL files and generated plans.
Handles discovery and organization of PDDL domain and problem files.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional


class FileManager:
    """
    Manages file operations for PDDL files and generated plans.
    
    Main functionality:
    - find_pddl_files: for each domain file, associates a list of problem file paths with it
    - File reading/writing operations
    - Directory management
    """

    def __init__(self):
        """Initialize the FileManager."""
        pass

    def read_file(self, file_path: str) -> Optional[str]:
        """
        Read a file and return its contents.

        Args:
            file_path (str): Path to the file

        Returns:
            Optional[str]: Contents of the file or None if error
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None

        try:
            with open(file_path, "r", encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def save_file(self, output_file_path: str, content: str) -> bool:
        """
        Save content to a file.

        Args:
            output_file_path (str): Path to save the file
            content (str): Content to save

        Returns:
            bool: True if successful, False otherwise
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        try:
            with open(output_file_path, "w", encoding='utf-8') as f:
                f.write(content)
            print(f"Saved plan to {output_file_path}")
            return True
        except Exception as e:
            print(f"Error saving file {output_file_path}: {e}")
            return False

    def find_pddl_files(self, problems_path: str) -> List[Dict]:
        """
        Find all domain and problem files in the given directory structure.
        
        Expected structure:
        src/data/                       
        ├── tetris/                      # Domain folders
            ├── domain.pddl              # Domain definition
            ├── problem_01.pddl          # Problem instances  
            └── problem_02.pddl
            ...
        ...
        
        Args:
            problems_path (str): Path to data directory containing domain folders

        Returns:
            List[Dict]: List of dictionaries containing domain and problem file information
            
        Example return:
        [
            {
                "domain_path": "/path/to/tetris/domain.pddl",
                "domain_text": "(define (domain tetris) ...)",
                "domain_name": "tetris",
                "problem_paths": ["/path/to/tetris/problem_01.pddl", "/path/to/tetris/problem_02.pddl"]
            }
        ]
        """
        pddl_directories = []

        if not os.path.exists(problems_path):
            print(f"Problems path does not exist: {problems_path}")
            return pddl_directories

        print(f"Searching for PDDL domains in: {problems_path}")

        # Look for domain directories (tetris, citycar, logistics, etc.)
        try:
            for item in os.listdir(problems_path):
                domain_dir = os.path.join(problems_path, item)
                
                # Skip if not a directory or if it's a hidden/system directory
                if not os.path.isdir(domain_dir) or item.startswith('.'):
                    continue
                
                # Skip README and other non-domain directories
                if item.lower() in ['readme', 'docs', '__pycache__']:
                    continue
                
                print(f"Checking domain directory: {item}")
                
                # Look for domain files in this directory
                try:
                    files = os.listdir(domain_dir)
                except OSError as e:
                    print(f"Cannot access directory {domain_dir}: {e}")
                    continue
                
                # Find domain file with multiple naming patterns
                domain_file = None
                
                # Pattern 1: domain.pddl
                if "domain.pddl" in files:
                    domain_file = "domain.pddl"
                # Pattern 2: {domain_name}_domain.pddl (like tetris_domain.pddl)
                elif f"{item}_domain.pddl" in files:
                    domain_file = f"{item}_domain.pddl"
                # Pattern 3: any *_domain.pddl file
                else:
                    domain_files = [f for f in files if f.endswith("_domain.pddl")]
                    if domain_files:
                        domain_file = domain_files[0]
                
                if not domain_file:
                    print(f"No domain file found in {domain_dir}")
                    continue
                
                # Read domain content
                domain_path = os.path.join(domain_dir, domain_file)
                domain_text = self.read_file(domain_path)
                if domain_text is None:
                    print(f"Failed to read domain file: {domain_path}")
                    continue
                
                # Find problem files (all .pddl files except the domain file)
                problem_files = [f for f in files if f.endswith(".pddl") and f != domain_file]
                
                if not problem_files:
                    print(f"No problem files found in {domain_dir}")
                    continue
                
                # Create problem paths and sort them
                problem_paths = [os.path.join(domain_dir, f) for f in problem_files]
                problem_paths.sort()
                
                # Use directory name as domain name
                domain_name = item
                
                # Add to results
                pddl_directories.append({
                    "domain_path": domain_path,
                    "domain_text": domain_text,
                    "domain_name": domain_name,
                    "problem_paths": problem_paths,
                })
                
                print(f"Found domain '{domain_name}' with {len(problem_paths)} problems")
                
        except OSError as e:
            print(f"Error accessing problems directory {problems_path}: {e}")
            return pddl_directories

        print(f"Total domains discovered: {len(pddl_directories)}")
        return pddl_directories

    def ensure_directory_exists(self, directory_path: str) -> bool:
        """
        Ensure that a directory exists, creating it if necessary.
        
        Args:
            directory_path (str): Path to directory
            
        Returns:
            bool: True if directory exists or was created successfully
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {directory_path}: {e}")
            return False
            
    def list_files(self, directory_path: str, extension: str = None) -> List[str]:
        """
        List files in a directory, optionally filtered by extension.
        
        Args:
            directory_path (str): Path to directory
            extension (str, optional): File extension filter (e.g., ".pddl")
            
        Returns:
            List[str]: List of file paths
        """
        if not os.path.exists(directory_path):
            return []
            
        try:
            files = []
            for file in os.listdir(directory_path):
                file_path = os.path.join(directory_path, file)
                if os.path.isfile(file_path):
                    if extension is None or file.endswith(extension):
                        files.append(file_path)
            return sorted(files)
        except Exception as e:
            print(f"Error listing files in {directory_path}: {e}")
            return []