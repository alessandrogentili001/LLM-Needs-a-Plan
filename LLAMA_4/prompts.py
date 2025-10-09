baseline = """
Problem description: you are an AI agent capable of solving Tetris planning problems using PDDL syntax.
In this problem, there is a grid with different Tetris pieces (single squares, two-straight pieces, and L-shaped pieces).
The agent can move these pieces to achieve a specific configuration goal.
"""

def tetris_problem_prompt(domain, problem):
    return f"""{baseline}

=== DOMAIN DEFINITION ===
{domain}

=== PROBLEM DEFINITION ===
{problem}

Can you BUILD A PLAN to solve this Tetris configuration?
Do not include any narrative or explanation—output only the chosen actions for the PLAN.
The actions should have no ':action' prefix since it is in the domain definition and should not be outputted in the plan text.
Each action should specify the piece being moved and the positions involved.
"""


# version_1 = """You are an expert PDDL planner specialized in Tetris-like spatial reasoning problems.

# Your input includes:
# - A Tetris domain with three types of pieces: one_square, two_straight, and right_l
# - A grid represented by positions and their connections
# - An initial configuration showing where pieces are placed
# - A goal configuration to achieve
# - Movement actions with specific preconditions and effects

# Key considerations:
# 1. Track which positions are clear (empty) vs occupied
# 2. Respect connectivity constraints - pieces can only move to connected positions
# 3. Different pieces have different movement costs: one_square (1), two_straight (2), right_l (3)
# 4. L-shaped pieces have directional movements (right, left, up, down) with complex position requirements
# 5. Always verify preconditions before selecting an action
# 6. Maintain spatial consistency throughout the plan

# Your output should be a valid sequence of actions that transforms the initial state to the goal state.
# Do not include any narrative or explanation—output only the plan.
# Format: action_name parameters
# """


# def tetris_problem_prompt_v1(domain, problem):
#     return f"""{version_1}

# === DOMAIN DEFINITION ===
# {domain}

# === PROBLEM DEFINITION ===
# {problem}

# Can you BUILD A PLAN to solve this Tetris configuration?
# Do not include any narrative or explanation—output only the chosen actions for the PLAN.
# The actions should have no ':action' prefix since it is in the domain definition and should not be outputted in the plan text.
# Each action should specify the piece being moved and the positions involved.
# """


# # Backprompt per correzione errori Tetris
# def tetris_backprompt(original_prompt, plan, reason):
#     return f"""Your previous Tetris plan was INVALID. 

# ORIGINAL PROBLEM:
# {original_prompt}

# YOUR PLAN:
# {plan}

# VALIDATION ERROR:
# {reason}

# Common issues in Tetris planning:
# - Moving pieces to positions that are not clear
# - Moving pieces to non-connected positions
# - Incorrect position parameters for L-shaped pieces
# - Violating the spatial constraints of piece shapes
# - Wrong direction for L-piece movements

# Please generate a new plan that ADDRESSES this issue.
# Consider the spatial layout carefully and verify each action's preconditions.
# Output only the corrected action sequence.
# """


# # Prompt con Chain of Thought per Tetris 
# # TODO: baseline or version_1
# def tetris_cot_prompt(domain, problem): 
#     return f"""{baseline} 

# === DOMAIN DEFINITION ===
# {domain}

# === PROBLEM DEFINITION ===
# {problem}

# Can you BUILD A PLAN to solve this Tetris puzzle?
# Let's reason step by step:
# 1. Identify the current position of each piece
# 2. Identify the goal positions for each piece
# 3. Determine which pieces need to move and in what order
# 4. Consider spatial constraints and connectivity
# 5. Plan moves that don't block other required movements

# Output only the final action sequence without the reasoning steps.
# """


# # Prompt per validazione incrementale Tetris
# # TODO: baseline or version_1
# def tetris_planner_validator_prompt(domain, problem):
#     return f"""{baseline}

# === DOMAIN DEFINITION ===
# {domain}

# === PROBLEM DEFINITION ===
# {problem}

# Solve this Tetris planning problem step by step.
# Respond with only ONE action at a time. 
# After each action, you will receive:
# - "Valid" along with the updated grid state if the action is correct
# - "Wrong" if the action violates preconditions or constraints

# Continue proposing actions until the goal is reached.
# """





# # Prompt con ottimizzazione del costo
# def tetris_optimized_prompt(domain, problem):
#     return f"""{baseline}

# === DOMAIN DEFINITION ===
# {domain}

# === PROBLEM DEFINITION ===
# {problem}

# Can you BUILD AN OPTIMIZED PLAN for this Tetris puzzle?

# Cost considerations:
# - Moving one_square pieces costs 1
# - Moving two_straight pieces costs 2
# - Moving right_l pieces costs 3

# Try to minimize the total cost while achieving the goal.
# Prefer moving smaller pieces when possible.
# Consider the order of moves to avoid unnecessary repositioning.

# Output only the action sequence that achieves the goal with minimal total cost.
# """
