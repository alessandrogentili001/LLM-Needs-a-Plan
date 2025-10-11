"""
PDDL Plan Validator using VAL (Validation and Analysis of PDDL)

Simple wrapper for VAL validator - the standard tool for PDDL plan validation.
VAL Repository: https://github.com/KCL-Planning/VAL
"""

import subprocess
import tempfile
import os
from typing import Dict


def validate_plan(domain_path: str, problem_path: str, plan_path: str, val_executable: str = "validate") -> Dict:
    """
    Validate a PDDL plan using VAL.
    
    Args:
        domain_path (str): Path to the PDDL domain file
        problem_path (str): Path to the PDDL problem file
        plan_path (str): Path to the plan file to validate
        val_executable (str): VAL executable name or path (default: "validate")
        
    Returns:
        Dict: {"valid": bool, "error": str or None}
    """
    try:
        # Run VAL: validate domain.pddl problem.pddl plan.txt
        result = subprocess.run(
            [val_executable, domain_path, problem_path, plan_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # VAL returns 0 for valid plans, non-zero for invalid
        is_valid = result.returncode == 0
        
        return {
            "valid": is_valid,
            "error": result.stderr.strip() if not is_valid and result.stderr else None
        }
        
    except FileNotFoundError:
        return {
            "valid": False,
            "error": f"VAL executable '{val_executable}' not found. Please install VAL."
        }
    except subprocess.TimeoutExpired:
        return {
            "valid": False,
            "error": "VAL validation timeout"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"VAL execution error: {str(e)}"
        }


def validate_plan_from_text(domain_path: str, problem_path: str, plan_text: str, val_executable: str = "validate") -> Dict:
    """
    Validate a plan from text content by creating a temporary plan file.
    
    Args:
        domain_path (str): Path to domain file
        problem_path (str): Path to problem file
        plan_text (str): Plan content as text
        val_executable (str): VAL executable name or path
        
    Returns:
        Dict: {"valid": bool, "error": str or None}
    """
    try:
        # Create temporary plan file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.plan', delete=False, encoding='utf-8') as temp_plan:
            temp_plan.write(plan_text)
            temp_plan_path = temp_plan.name
        
        # Validate using VAL
        result = validate_plan(domain_path, problem_path, temp_plan_path, val_executable)
        
        # Clean up
        try:
            os.unlink(temp_plan_path)
        except OSError:
            pass
            
        return result
        
    except Exception as e:
        return {
            "valid": False,
            "error": f"Error creating temporary plan file: {str(e)}"
        }