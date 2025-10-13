#!/bin/bash
# LLM-Needs-a-Plan Experiment Management Script
# This script provides a simple interface to the experiment framework

PROJECT_ROOT="/home/aless/PROJECTS/LLM-Needs-a-Plan"
EXPERIMENTS_DIR="$PROJECT_ROOT/experiments"
CONFIG_FILE="$EXPERIMENTS_DIR/configs/experiment_config.yml"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

usage() {
    echo "LLM-Needs-a-Plan Experiment Manager"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  list                    - List available experiment sets"
    echo "  generate <set>          - Generate experiment scripts"
    echo "  generate <set> --dry    - Preview experiments without generating"
    echo "  submit <set>            - Submit experiments to cluster"
    echo "  monitor <set>           - Monitor experiment progress"
    echo "  status                  - Show overall status"
    echo
    echo "Available experiment sets:"
    echo "  quick_test             - Fast validation (2 experiments)"
    echo "  model_comparison       - Compare Phi4 vs Llama4 (12 experiments)"
    echo "  domain_analysis        - Full domain coverage (11 experiments)"
    echo "  comprehensive          - Complete matrix (22 experiments)"
}

list_experiments() {
    echo -e "${BLUE}Available Experiment Sets:${NC}"
    echo
    if [ -f "$CONFIG_FILE" ]; then
        python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
    
for name, details in config['experiment_sets'].items():
    models = details['models']
    domains = details['domains']
    priority = details['priority']
    desc = details['description']
    print(f'  {name:20} Priority: {priority}  Models: {len(models)}  Domains: {len(domains)}')
    print(f'  {\" \" * 20} {desc}')
    print()
"
    else
        echo -e "${RED}Configuration file not found: $CONFIG_FILE${NC}"
        exit 1
    fi
}

generate_experiments() {
    local experiment_set=$1
    local dry_run=$2
    
    echo -e "${BLUE}Generating experiments for: ${experiment_set}${NC}"
    
    cd "$PROJECT_ROOT"
    
    if [ "$dry_run" = "--dry" ]; then
        python3 experiments/generate_experiments.py \
            -c "$CONFIG_FILE" \
            -e "$experiment_set" \
            -b "$PROJECT_ROOT" \
            --dry_run
    else
        python3 experiments/generate_experiments.py \
            -c "$CONFIG_FILE" \
            -e "$experiment_set" \
            -b "$PROJECT_ROOT"
            
        echo
        echo -e "${GREEN}✓ Scripts generated successfully!${NC}"
        echo -e "${YELLOW}Next steps:${NC}"
        echo "  Submit: $0 submit $experiment_set"
        echo "  Monitor: $0 monitor $experiment_set"
    fi
}

submit_experiments() {
    local experiment_set=$1
    local submit_script="$EXPERIMENTS_DIR/scripts/submit_${experiment_set}.sh"
    
    if [ ! -f "$submit_script" ]; then
        echo -e "${RED}Submit script not found: $submit_script${NC}"
        echo "Generate experiments first: $0 generate $experiment_set"
        exit 1
    fi
    
    echo -e "${BLUE}Submitting experiments: ${experiment_set}${NC}"
    
    cd "$PROJECT_ROOT"
    bash "$submit_script"
}

monitor_experiments() {
    local experiment_set=$1
    
    echo -e "${BLUE}Monitoring experiments: ${experiment_set}${NC}"
    
    cd "$PROJECT_ROOT"
    python3 experiments/simple_monitor.py -e "$experiment_set"
}

status_overview() {
    echo -e "${BLUE}=== LLM-Needs-a-Plan Status Overview ===${NC}"
    echo
    
    cd "$PROJECT_ROOT"
    
    # Check if experiments exist
    if [ -d "$EXPERIMENTS_DIR/scripts" ] && [ "$(ls -A $EXPERIMENTS_DIR/scripts)" ]; then
        echo -e "${GREEN}Generated Scripts:${NC}"
        ls "$EXPERIMENTS_DIR/scripts"/*.sh 2>/dev/null | wc -l | xargs echo "  SLURM scripts:"
        ls "$EXPERIMENTS_DIR/scripts"/submit_*.sh 2>/dev/null | sed 's/.*submit_/  - /' | sed 's/.sh$//'
        echo
    fi
    
    # Check results
    if [ -d "$EXPERIMENTS_DIR/results" ] && [ "$(ls -A $EXPERIMENTS_DIR/results)" ]; then
        echo -e "${GREEN}Available Results:${NC}"
        ls "$EXPERIMENTS_DIR/results" | wc -l | xargs echo "  Result directories:"
        ls "$EXPERIMENTS_DIR/results" | head -5 | sed 's/^/  - /'
        if [ $(ls "$EXPERIMENTS_DIR/results" | wc -l) -gt 5 ]; then
            echo "  ... and $(( $(ls "$EXPERIMENTS_DIR/results" | wc -l) - 5 )) more"
        fi
        echo
    fi
    
    # Overall monitoring
    python3 experiments/simple_monitor.py
}

# Main script logic
case "$1" in
    "list")
        list_experiments
        ;;
    "generate")
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Experiment set name required${NC}"
            echo "Usage: $0 generate <experiment_set> [--dry]"
            exit 1
        fi
        generate_experiments "$2" "$3"
        ;;
    "submit")
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Experiment set name required${NC}"
            echo "Usage: $0 submit <experiment_set>"
            exit 1
        fi
        submit_experiments "$2"
        ;;
    "monitor")
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Experiment set name required${NC}"
            echo "Usage: $0 monitor <experiment_set>"
            exit 1
        fi
        monitor_experiments "$2"
        ;;
    "status")
        status_overview
        ;;
    *)
        usage
        exit 1
        ;;
esac