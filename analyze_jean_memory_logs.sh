#!/bin/bash
# Jean Memory Log Analysis Script
# Extracts performance metrics from production logs

echo "📊 JEAN MEMORY PERFORMANCE LOG ANALYSIS"
echo "========================================"

LOG_FILE=${1:-production.log}

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo "Usage: $0 [log_file_path]"
    exit 1
fi

echo "📄 Analyzing log file: $LOG_FILE"
echo

# Performance milestones
echo "⏱️ PERFORMANCE MILESTONES:"
grep '\[PERF-TRACK\]' "$LOG_FILE" | tail -20 | jq -r '.milestone + ": " + (.elapsed_seconds | tostring) + "s"' 2>/dev/null || grep '\[PERF-TRACK\]' "$LOG_FILE" | tail -20
echo

# A/B test results  
echo "🧪 A/B TEST METRICS:"
grep '\[AB-TEST\]' "$LOG_FILE" | tail -10 | jq -r '.variant + " - " + (.processing_time_seconds | tostring) + "s"' 2>/dev/null || grep '\[AB-TEST\]' "$LOG_FILE" | tail -10
echo

# Orchestration summaries
echo "📈 ORCHESTRATION SUMMARIES:"
grep '\[PERF-SUMMARY\]' "$LOG_FILE" | tail -10 | jq -r '"Total: " + (.total_orchestration_time | tostring) + "s (AI: " + (.performance_breakdown.ai_planning | tostring) + "s)"' 2>/dev/null || grep '\[PERF-SUMMARY\]' "$LOG_FILE" | tail -10
echo

# Claude Haiku performance
echo "🚀 CLAUDE HAIKU PERFORMANCE:"
grep '\[CLAUDE-HAIKU\]' "$LOG_FILE" | grep "completed" | tail -20 | awk '{print $NF}' | sort -n
echo

# Error rates
echo "❌ ERROR ANALYSIS:"
echo "Total errors: $(grep -c 'ERROR\|❌' "$LOG_FILE")"
echo "Claude Haiku errors: $(grep -c '\[CLAUDE-HAIKU\].*failed' "$LOG_FILE")"
echo "Orchestration errors: $(grep -c 'Error in standard orchestration' "$LOG_FILE")"
echo

echo "✅ Analysis complete!"
