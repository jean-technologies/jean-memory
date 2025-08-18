#!/bin/bash

# Jean Memory Evaluation Infrastructure Setup Script
# ===================================================

echo "🚀 Setting up Jean Memory Evaluation Infrastructure..."

# Create evaluation metrics directory
mkdir -p ./evaluation_metrics

# Set environment variables for evaluation
export EVALUATION_MODE=${EVALUATION_MODE:-false}
export EVALUATION_ASYNC=${EVALUATION_ASYNC:-true}
export EVALUATION_MAX_MEMORY_MB=${EVALUATION_MAX_MEMORY_MB:-50}
export EVALUATION_TIMEOUT_SECONDS=${EVALUATION_TIMEOUT_SECONDS:-5.0}
export EVALUATION_STORAGE=${EVALUATION_STORAGE:-json}
export EVALUATION_STORAGE_PATH=${EVALUATION_STORAGE_PATH:-./evaluation_metrics}
export EVALUATION_LOG_LEVEL=${EVALUATION_LOG_LEVEL:-INFO}

echo "✅ Environment variables configured:"
echo "   EVALUATION_MODE=$EVALUATION_MODE"
echo "   EVALUATION_ASYNC=$EVALUATION_ASYNC"
echo "   EVALUATION_MAX_MEMORY_MB=$EVALUATION_MAX_MEMORY_MB"
echo "   EVALUATION_TIMEOUT_SECONDS=$EVALUATION_TIMEOUT_SECONDS"
echo "   EVALUATION_STORAGE=$EVALUATION_STORAGE"
echo "   EVALUATION_STORAGE_PATH=$EVALUATION_STORAGE_PATH"
echo "   EVALUATION_LOG_LEVEL=$EVALUATION_LOG_LEVEL"

# Function to enable evaluation
enable_evaluation() {
    export EVALUATION_MODE=true
    echo "✅ Evaluation mode ENABLED"
}

# Function to disable evaluation
disable_evaluation() {
    export EVALUATION_MODE=false
    echo "❌ Evaluation mode DISABLED"
}

# Function to run tests
run_tests() {
    echo "🧪 Running evaluation system tests..."
    python app/evaluation/test_evaluation.py
}

# Function to generate report
generate_report() {
    echo "📊 Generating evaluation report..."
    python -c "
from app.evaluation import MetricsStorage
storage = MetricsStorage()
report_path = storage.export_report('evaluation_report.md')
print(f'Report generated: {report_path}')
"
}

# Function to clear metrics
clear_metrics() {
    echo "🗑️ Clearing evaluation metrics..."
    rm -rf ./evaluation_metrics/*.jsonl
    echo "✅ Metrics cleared"
}

# Print usage information
echo ""
echo "📖 Usage Instructions:"
echo "   To enable evaluation:  source setup_evaluation.sh && enable_evaluation"
echo "   To disable evaluation: source setup_evaluation.sh && disable_evaluation"
echo "   To run tests:         ./setup_evaluation.sh test"
echo "   To generate report:   ./setup_evaluation.sh report"
echo "   To clear metrics:     ./setup_evaluation.sh clear"
echo ""

# Handle command line arguments
case "$1" in
    test)
        run_tests
        ;;
    report)
        generate_report
        ;;
    clear)
        clear_metrics
        ;;
    enable)
        enable_evaluation
        ;;
    disable)
        disable_evaluation
        ;;
    *)
        echo "ℹ️ Evaluation infrastructure ready. Use 'source setup_evaluation.sh' to load functions."
        ;;
esac