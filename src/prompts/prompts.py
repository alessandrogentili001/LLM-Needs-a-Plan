"""
PDDL Planning Prompts

Collection of prompts for PDDL planning tasks with different LLMs.
Includes system prompts, domain-specific prompts, and specialized prompt variants.
"""

# System prompt for PDDL planning tasks
system_prompt_pddl = """You are an expert AI planning assistant specialized in PDDL (Planning Domain Definition Language).

Your expertise includes:
- Analyzing PDDL domain definitions and problem specifications
- Understanding preconditions and effects of actions
- Generating valid, executable action sequences
- Optimizing plans for efficiency and correctness
- Spatial reasoning for configuration problems

When solving planning problems:
1. Carefully analyze the domain actions and their requirements
2. Understand the initial state and goal conditions
3. Plan step-by-step to achieve the goal state
4. Ensure all action preconditions are satisfied before execution
5. Consider the effects of each action on the world state

Output format:
- Provide only the action sequence without explanations unless requested
- Use correct PDDL action syntax: (action-name param1 param2 ...)
- Do not include :action prefixes in the plan output
- Ensure the plan is executable and achieves the goal

If a problem appears unsolvable, clearly explain why."""

# Base prompt template for Tetris problems
tetris_baseline = """
Problem description: you are an AI agent capable of solving Tetris planning problems using PDDL syntax.
In this problem, there is a grid with different Tetris pieces (single squares, two-straight pieces, and L-shaped pieces).
The agent can move these pieces to achieve a specific configuration goal.
"""

def tetris_problem_prompt(domain: str, problem: str) -> str:
    """
    Generate a prompt for Tetris planning problems.
    
    Args:
        domain (str): PDDL domain definition
        problem (str): PDDL problem definition
        
    Returns:
        str: Formatted prompt for the model
    """
    return f"""{tetris_baseline}

=== DOMAIN DEFINITION ===
{domain}

=== PROBLEM DEFINITION ===
{problem}

Can you BUILD A PLAN to solve this Tetris configuration?
Do not include any narrative or explanation—output only the chosen actions for the PLAN.
The actions should have no ':action' prefix since it is in the domain definition and should not be outputted in the plan text.
Each action should specify the piece being moved and the positions involved."""

def generic_pddl_prompt(domain: str, problem: str) -> str:
    """
    Generate a generic prompt for any PDDL planning problem.
    
    Args:
        domain (str): PDDL domain definition
        problem (str): PDDL problem definition
        
    Returns:
        str: Formatted prompt for the model
    """
    return f"""Please solve this PDDL planning problem.

=== DOMAIN DEFINITION ===
{domain}

=== PROBLEM DEFINITION ===  
{problem}

Generate a valid plan that transforms the initial state to the goal state.
Output only the sequence of actions needed to solve the problem.
Each action should be in the format: (action-name param1 param2 ...)"""

def chain_of_thought_prompt(domain: str, problem: str) -> str:
    """
    Generate a Chain of Thought prompt for complex planning problems.
    
    Args:
        domain (str): PDDL domain definition
        problem (str): PDDL problem definition
        
    Returns:
        str: CoT formatted prompt for the model
    """
    return f"""Solve this PDDL planning problem step by step.

=== DOMAIN DEFINITION ===
{domain}

=== PROBLEM DEFINITION ===
{problem}

Let's think through this step by step:
1. First, analyze the initial state and identify what objects are where
2. Identify the goal conditions that need to be satisfied
3. Determine which actions are available and their preconditions
4. Plan the sequence of actions needed to reach the goal
5. Verify that each action's preconditions are met

Please show your reasoning process, then provide the final action sequence."""

def validation_feedback_prompt(original_prompt: str, plan: str, validation_error: str) -> str:
    """
    Generate a feedback prompt for plan correction after validation failure.
    
    Args:
        original_prompt (str): Original planning prompt
        plan (str): The invalid plan that was generated
        validation_error (str): Error message from validation
        
    Returns:
        str: Feedback prompt for plan correction
    """
    return f"""Your previous plan was INVALID according to the validator.

ORIGINAL PROBLEM:
{original_prompt}

YOUR PLAN:
{plan}

VALIDATION ERROR:
{validation_error}

Common issues in PDDL planning:
- Action preconditions not satisfied
- Incorrect parameter ordering
- Using unavailable objects or actions
- Goal conditions not properly achieved
- State conflicts between actions

Please generate a corrected plan that addresses this validation error.
Output only the corrected action sequence."""

def optimization_prompt(domain: str, problem: str) -> str:
    """
    Generate a prompt focused on plan optimization.
    
    Args:
        domain (str): PDDL domain definition
        problem (str): PDDL problem definition
        
    Returns:
        str: Optimization-focused prompt
    """
    return f"""Solve this PDDL planning problem with focus on optimization.

=== DOMAIN DEFINITION ===
{domain}

=== PROBLEM DEFINITION ===
{problem}

Generate an OPTIMAL plan that:
1. Achieves the goal with minimum number of actions
2. Considers action costs if specified in the domain
3. Avoids unnecessary intermediate steps
4. Uses efficient action ordering

Output the most efficient action sequence to solve the problem."""

def incremental_planning_prompt(domain: str, problem: str) -> str:
    """
    Generate a prompt for incremental/interactive planning.
    
    Args:
        domain (str): PDDL domain definition
        problem (str): PDDL problem definition
        
    Returns:
        str: Incremental planning prompt
    """
    return f"""Solve this PDDL planning problem incrementally.

=== DOMAIN DEFINITION ===
{domain}

=== PROBLEM DEFINITION ===
{problem}

Propose ONE action at a time. After each action, you will receive feedback:
- "Valid" with updated state if the action is correct
- "Invalid" with error explanation if the action fails

Continue proposing actions until the goal is achieved.
Start with the first action now."""

# Utility functions for prompt customization
def add_constraints_to_prompt(base_prompt: str, constraints: list) -> str:
    """Add custom constraints to a base prompt."""
    constraints_text = "\n".join(f"- {constraint}" for constraint in constraints)
    return f"""{base_prompt}

Additional constraints:
{constraints_text}

Please ensure your plan respects all constraints."""

def add_examples_to_prompt(base_prompt: str, examples: list) -> str:
    """Add example solutions to a base prompt."""
    examples_text = "\n\n".join(f"Example {i+1}:\n{example}" for i, example in enumerate(examples))
    return f"""{base_prompt}

Examples of similar problems:
{examples_text}

Now solve the given problem following a similar approach."""