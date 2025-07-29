import asyncio
import logging
import time
import re
import numpy as np
import os
import sys

# Add project root to path to allow module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from openmemory.api.app.tools.orchestration import jean_memory
from unittest.mock import patch

# --- Test Configuration ---
NUM_ITERATIONS = 20
P95_LATENCY_TARGET_MS = 3000

# --- Test Scenarios ---
SCENARIOS = [
    {
        "name": "Simple Context Query",
        "message": "What was the last thing I mentioned about the 'Aquila' project?",
        "is_new": False,
        "needs_context": True
    },
    {
        "name": "Broader Question",
        "message": "What are my main goals for this quarter?",
        "is_new": False,
        "needs_context": True
    },
    {
        "name": "New Conversation Starter",
        "message": "Hey, it's been a while. What should I be focusing on?",
        "is_new": True,
        "needs_context": True
    }
]

# --- Logging Setup ---
# Use a in-memory stream to capture logs for parsing
from io import StringIO
log_stream = StringIO()

# Clear any existing handlers
logging.getLogger().handlers = []
logging.basicConfig(level=logging.INFO, format='%(message)s', stream=log_stream)


def parse_perf_logs(log_contents: str) -> dict:
    """Parses performance logs and aggregates the results."""
    # Regex to find all [PERF] logs and extract the description and time
    perf_log_pattern = re.compile(r"\[PERF\]\s(.*?)\s+took\s+([\d\.]+s)")
    
    # Structure to hold all timings for each metric
    timings = {
        "Total jean_memory call": [],
        "AI Plan Creation": [],
        "Context Execution": [],
        "Context Formatting": [],
        "Standard Orchestration": [],
        "Life Narrative V2": [],
    }

    for line in log_contents.splitlines():
        match = perf_log_pattern.search(line)
        if match:
            description = match.group(1).strip()
            # Convert time string "X.XXXXs" to milliseconds
            duration_ms = float(match.group(2).replace('s', '')) * 1000
            
            if description in timings:
                timings[description].append(duration_ms)

    return timings


def calculate_statistics(timings: dict) -> dict:
    """Calculates avg, median, and P95 for each metric."""
    stats = {}
    for metric, values in timings.items():
        if values:
            stats[metric] = {
                "avg": f"{np.mean(values):.2f} ms",
                "median": f"{np.median(values):.2f} ms",
                "p95": f"{np.percentile(values, 95):.2f} ms",
                "runs": len(values)
            }
    return stats


async def run_benchmarks():
    """Runs the benchmark scenarios and prints the results."""
    print(f"🚀 Running Fast Path Benchmarks ({NUM_ITERATIONS} iterations per scenario)...")
    
    # Mock the background tasks so we only measure the synchronous fast path
    with patch('openmemory.api.app.tools.orchestration.background_tasks_var') as mock_bg_tasks:
        mock_bg_tasks.get.return_value.add_task.return_value = None

        for scenario in SCENARIOS:
            print(f"\n--- Scenario: {scenario['name']} ---")
            for i in range(NUM_ITERATIONS):
                print(f"  Running iteration {i+1}/{NUM_ITERATIONS}...", end='\\r')
                await jean_memory(
                    user_message=scenario["message"],
                    is_new_conversation=scenario["is_new"],
                    needs_context=scenario["needs_context"]
                )
                # Small sleep to avoid overwhelming the system
                await asyncio.sleep(0.1)
            print("\\n")

    print("✅ Benchmarking complete.")

    # --- Analyze and Report Results ---
    log_contents = log_stream.getvalue()
    timings = parse_perf_logs(log_contents)
    statistics = calculate_statistics(timings)

    print("\\n--- Performance Report ---")
    for metric, stats in statistics.items():
        print(f"Metric: {metric}")
        print(f"  Avg: {stats['avg']}, Median: {stats['median']}, P95: {stats['p95']} (from {stats['runs']} runs)")

    # --- Assertions ---
    p95_total = float(statistics.get("Total jean_memory call", {}).get("p95", "0.0 ms").split()[0])
    
    print(f"\\n--- Verification ---")
    print(f"P95 Latency for 'Total jean_memory call': {p95_total:.2f} ms")
    print(f"Target: {P95_LATENCY_TARGET_MS} ms")

    assert p95_total < P95_LATENCY_TARGET_MS, f"P95 latency ({p95_total:.2f}ms) exceeds target of {P95_LATENCY_TARGET_MS}ms!"

    print("✅ Success: P95 latency is within the target.")


if __name__ == "__main__":
    # Mock user and client context
    from openmemory.api.app.context import user_id_var, client_name_var
    user_id_var.set("benchmark_user")
    client_name_var.set("benchmark_client")

    asyncio.run(run_benchmarks()) 