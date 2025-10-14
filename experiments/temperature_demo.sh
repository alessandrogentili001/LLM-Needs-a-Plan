#!/bin/bash
# Temperature Sensitivity Study - Quick Demo
# Step-by-step demonstration of focused temperature analysis

set -e

PROJECT_ROOT="/home/aless/PROJECTS/LLM-Needs-a-Plan"
EXPERIMENTS_DIR="$PROJECT_ROOT/experiments"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd "$EXPERIMENTS_DIR"

echo -e "${BLUE}🌡️ Temperature Sensitivity Study - Quick Demo${NC}"
echo "=================================================="
echo ""

echo -e "${YELLOW}📋 Step 1: Review Temperature Experiment Configuration${NC}"
if [ -f "configs/temperature_experiment.yml" ]; then
    echo "✅ Temperature configuration found"
    
    echo ""
    echo "Key configuration highlights:"
    python3 -c "
import yaml
with open('configs/temperature_experiment.yml', 'r') as f:
    config = yaml.safe_load(f)

print('🎯 Research Goal:', config['experiment']['title'])
print('🌡️  Temperatures:', [t['value'] for t in config['model']['temperature_values']])
print('🏗️  Domains:', list(config['experimental_design']['domains'].keys()))
print('🔬 Hypothesis:', config['experiment']['research_hypothesis'][:100] + '...')
"
else
    echo "❌ Temperature configuration not found!"
    exit 1
fi

echo -e "\n${YELLOW}📋 Step 2: Generate Temperature Experiments${NC}"

echo "🚀 Generating full temperature sensitivity study..."
python3 temperature_generator.py --config configs/temperature_experiment.yml --phase full

# Show generated experiment structure if experiments were created
if [ -d "results" ]; then
    LATEST_TEMP_DIR=$(ls -td results/temperature_analysis_* 2>/dev/null | head -1)
    if [ -n "$LATEST_TEMP_DIR" ]; then
        echo ""
        echo -e "${BLUE}📁 Generated Experiment Structure:${NC}"
        echo "Base directory: $LATEST_TEMP_DIR"
        
        echo ""
        echo "Directory structure:"
        ls -la "$LATEST_TEMP_DIR" | head -10
        
        echo ""
        echo "Generated scripts:"
        SCRIPT_COUNT=$(ls "$LATEST_TEMP_DIR"/scripts/*.sh 2>/dev/null | wc -l)
        echo "  📄 SLURM scripts: $SCRIPT_COUNT"
        
        if [ -f "$LATEST_TEMP_DIR/submit_experiments.sh" ]; then
            echo -e "\n${GREEN}🚀 Ready to submit experiments!${NC}"
            echo "Use: $LATEST_TEMP_DIR/submit_experiments.sh"
        fi
        
        echo ""
        echo -e "${YELLOW}📋 Step 3: Analysis Preparation${NC}"
        echo "After experiments complete, analyze results with:"
        echo "  python3 temperature_analyzer.py $LATEST_TEMP_DIR"
        echo ""
        echo "This will generate:"
        echo "  • Statistical analysis of temperature effects"
        echo "  • Performance visualizations"  
        echo "  • Comprehensive HTML report"
        echo "  • Optimal temperature recommendations"
    fi
fi

echo ""
echo -e "${BLUE}📚 Temperature Study Workflow Summary:${NC}"
echo "1. ✅ Configuration reviewed"
echo "2. 🔧 Experiments generated" 
echo "3. 🚀 Submit experiments (manual step)"
echo "4. 📊 Analyze results (after completion)"
echo "5. 📋 Generate research report"

echo ""
echo -e "${GREEN}🎯 Research Value:${NC}"
echo "This systematic temperature study will provide:"
echo "  • Optimal temperature identification for Phi4 planning"
echo "  • Statistical validation of temperature effects"
echo "  • Domain-specific temperature recommendations"
echo "  • Reproducible methodology for future studies"

echo ""
echo -e "${BLUE}🔬 Analytical Rigor Features:${NC}"

# Read actual replication info from config
RUNS_PER_CONDITION=$(python3 -c "
import yaml
with open('configs/temperature_experiment.yml', 'r') as f:
    config = yaml.safe_load(f)
runs = config['experimental_design']['replication']['runs_per_condition']
print(runs)
")

echo "  • Controlled experimental design"
if [ "$RUNS_PER_CONDITION" -eq 1 ]; then
    echo "  • Single run per condition (exploratory analysis)"
else
    echo "  • $RUNS_PER_CONDITION replications per condition"
fi
echo "  • Statistical significance testing"
echo "  • Confidence interval calculation"
echo "  • Publication-ready visualizations"