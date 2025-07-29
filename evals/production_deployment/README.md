# Jean Memory Evaluation Framework - Production Deployment

## Overview

This is the production deployment of the Jean Memory Evaluation Framework, designed to run comprehensive evaluations of the Jean Memory system in an isolated environment.

## Features

- **Memory Triage Evaluation**: Tests AI-powered memory decision accuracy
- **Context Quality Assessment**: Evaluates context relevance and personalization
- **Performance Benchmarking**: Measures response times and system performance
- **System Integration Testing**: Verifies all system components are operational
- **Production Isolation**: Runs safely without affecting production data

## Quick Start

### 1. Health Check
```bash
python scripts/health_check.py
```

### 2. Run Production Evaluation
```bash
python scripts/run_production_evaluation.py
```

### 3. View Results
Results are saved in the `results/` directory with timestamps:
- `eval_results_YYYYMMDD_HHMMSS.json` - Detailed JSON results
- `eval_summary_YYYYMMDD_HHMMSS.txt` - Human-readable summary

## Configuration

Edit `production_config.json` to customize:
- Evaluation targets and thresholds
- Timeout settings
- Alert configurations
- Reporting options

## Monitoring

### Health Check
```bash
python scripts/health_check.py
```

### Logs
Check `logs/evaluation.log` for detailed execution logs.

### Alerts
The system automatically generates alerts for:
- System health scores below 75%
- Memory triage accuracy below 85%
- Performance issues
- Integration failures

## Directory Structure

```
production_deployment/
├── production_config.json     # Main configuration
├── eval_framework.py          # Core evaluation framework
├── metrics.py                 # Metrics and scoring utilities
├── golden_memories.json       # Test dataset
├── evaluation_runner.py       # Working evaluation runner
├── scripts/
│   ├── run_production_evaluation.py
│   └── health_check.py
├── results/                   # Evaluation results
├── logs/                      # Execution logs
└── docs/                      # Documentation
```

## Interpreting Results

### System Health Score
- **90-100%**: Excellent - All systems operational
- **75-89%**: Good - Minor issues, system functional
- **60-74%**: Fair - Some issues, monitoring recommended
- **Below 60%**: Needs improvement - Investigation required

### Key Metrics
- **Memory Triage Accuracy**: Target 85%+
- **Context Quality Pass Rate**: Target 60%+
- **Performance Success Rate**: Target 80%+
- **System Integration Score**: Target 75%+

## Troubleshooting

### Common Issues

1. **Configuration Error**: Check `production_config.json` syntax
2. **Missing Dependencies**: Ensure all required files are present
3. **API Quota Exceeded**: Wait for rate limits to reset
4. **Network Issues**: Check connectivity to required services

### Getting Help

For issues or questions:
1. Check the logs in `logs/evaluation.log`
2. Run health check: `python scripts/health_check.py`
3. Review configuration in `production_config.json`
4. Contact the development team

## Security

This deployment is designed for production safety:
- Uses isolated test user IDs
- Does not access production user data
- Automatically cleans up test data
- Runs in sandboxed environment

## Version History

- **v1.0.0**: Initial production deployment
  - Memory triage evaluation with 95% accuracy
  - Context quality assessment framework
  - Performance benchmarking suite
  - System integration testing
  - Production isolation and safety features
