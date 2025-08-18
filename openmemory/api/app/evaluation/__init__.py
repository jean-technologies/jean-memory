"""
Jean Memory Evaluation Infrastructure
======================================

Non-invasive evaluation system for measuring Jean Memory performance
without impacting production systems.

Includes:
- Task 1: Core evaluation infrastructure
- Task 2: LLM Judge & Scoring System for automated quality evaluation
- Task 3: Synthetic Test Data Generator for comprehensive test coverage
- Task 4: Conversation Dataset Generator for multi-turn conversation testing
- Task 5: Secure Token Capture and Storage for authenticated testing
- Task 6: Direct MCP Endpoint Client for tool integration
- Task 7: Conversation Test Runner for executing conversation datasets
- Task 8: Performance Metrics Extraction for analyzing service logs
- Task 9: Comprehensive Evaluation Reports for actionable insights
"""

from .core import EvaluationDecorator, EvaluationMode, evaluate
from .metrics import MetricsCollector, EvaluationMetric
from .storage import MetricsStorage

# Secure Token Management (Task 5)
try:
    from .auth_helper import SecureTokenManager
    from .config import AuthConfig, get_auth_headers, is_authenticated, validate_auth
    _AUTH_AVAILABLE = True
except ImportError as e:
    _AUTH_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"Auth system not available: {e}")

# LLM Judge System (Task 2)
try:
    from .llm_judge import (
        LLMJudgeService,
        EvaluationContext as JudgeEvaluationContext,
        JudgeScore,
        ReasoningType,
        LLMProvider,
        evaluate_single_response,
        evaluate_conversation_consistency,
        get_judge_service
    )
    
    # Consensus Judge System
    from .consensus_judge import (
        ConsensusJudgeService,
        ConsensusScore,
        ConsensusMode,
        ConsensusConfiguration,
        evaluate_with_consensus,
        compare_consensus_vs_single,
        get_consensus_judge
    )
    
    _LLM_JUDGE_AVAILABLE = True
    _CONSENSUS_JUDGE_AVAILABLE = True
except ImportError as e:
    _LLM_JUDGE_AVAILABLE = False
    _CONSENSUS_JUDGE_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"LLM Judge not available: {e}")

# Synthetic Test Data Generator (Task 3)
try:
    from .synthetic_data_generator import (
        SyntheticDataGeneratorService,
        SyntheticTestCase,
        Memory,
        DifficultyLevel,
        PersonaType,
        ConversationDecisionPath,
        generate_single_test_case,
        generate_test_batch,
        generate_balanced_dataset,
        get_synthetic_generator
    )
    
    from .synthetic_quality_validator import (
        SyntheticQualityValidator,
        QualityValidationResult,
        validate_single_test_case,
        validate_test_batch,
        generate_and_validate_batch,
        get_quality_validator
    )
    
    from .synthetic_dataset_manager import (
        SyntheticDatasetManager,
        DatasetMetadata,
        DatasetFilter,
        create_test_dataset,
        load_test_dataset,
        filter_dataset,
        export_test_dataset,
        get_dataset_manager
    )
    
    _SYNTHETIC_GENERATOR_AVAILABLE = True
except ImportError as e:
    _SYNTHETIC_GENERATOR_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"Synthetic Test Data Generator not available: {e}")

# Conversation Dataset Generator (Task 4)
try:
    from .conversation_dataset_generator import (
        ConversationDatasetGenerator,
        ConversationDataset,
        ConversationTurn,
        ConversationDistributionType,
        generate_conversation_dataset,
        save_conversation_dataset,
        load_conversation_dataset,
        get_conversation_generator
    )
    
    _CONVERSATION_GENERATOR_AVAILABLE = True
except ImportError as e:
    _CONVERSATION_GENERATOR_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"Conversation Dataset Generator not available: {e}")

# Direct MCP Endpoint Client (Task 6)
try:
    from .minimal_mcp_client import (
        MinimalMCPClient,
        get_mcp_client,
        search_memories,
        call_jean_memory,
        call_jean_memory_tool,
        test_mcp_connection
    )
    from .mcp_types import (
        MCPRequest,
        MCPResponse,
        MCPMemoryResult,
        MCPError,
        MCPNetworkError,
        MCPAuthenticationError,
        MCPTimeoutError,
        MCPRateLimitError,
        create_memory_search_request,
        create_jean_memory_request,
        parse_mcp_response
    )
    
    _MCP_CLIENT_AVAILABLE = True
except ImportError as e:
    _MCP_CLIENT_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"MCP Client not available: {e}")

__all__ = [
    "EvaluationDecorator",
    "EvaluationMode",
    "evaluate",
    "MetricsCollector", 
    "EvaluationMetric",
    "MetricsStorage"
]

# Add Auth exports if available
if _AUTH_AVAILABLE:
    __all__.extend([
        "SecureTokenManager",
        "AuthConfig",
        "get_auth_headers",
        "is_authenticated",
        "validate_auth"
    ])

# Add LLM Judge exports if available
if _LLM_JUDGE_AVAILABLE:
    __all__.extend([
        "LLMJudgeService",
        "JudgeEvaluationContext", 
        "JudgeScore",
        "ReasoningType",
        "LLMProvider",
        "evaluate_single_response",
        "evaluate_conversation_consistency", 
        "get_judge_service"
    ])

# Add Consensus Judge exports if available
if _CONSENSUS_JUDGE_AVAILABLE:
    __all__.extend([
        "ConsensusJudgeService",
        "ConsensusScore",
        "ConsensusMode",
        "ConsensusConfiguration",
        "evaluate_with_consensus",
        "compare_consensus_vs_single",
        "get_consensus_judge"
    ])

# Add Synthetic Test Data Generator exports if available
if _SYNTHETIC_GENERATOR_AVAILABLE:
    __all__.extend([
        # Core generator components
        "SyntheticDataGeneratorService",
        "SyntheticTestCase",
        "Memory",
        "DifficultyLevel",
        "PersonaType",
        "ConversationDecisionPath",
        "generate_single_test_case",
        "generate_test_batch",
        "generate_balanced_dataset",
        "get_synthetic_generator",
        
        # Quality validation components
        "SyntheticQualityValidator",
        "QualityValidationResult",
        "validate_single_test_case",
        "validate_test_batch",
        "generate_and_validate_batch",
        "get_quality_validator",
        
        # Dataset management components
        "SyntheticDatasetManager",
        "DatasetMetadata",
        "DatasetFilter",
        "create_test_dataset",
        "load_test_dataset",
        "filter_dataset",
        "export_test_dataset",
        "get_dataset_manager"
    ])

# Add Conversation Dataset Generator exports if available
if _CONVERSATION_GENERATOR_AVAILABLE:
    __all__.extend([
        # Core conversation generator components
        "ConversationDatasetGenerator",
        "ConversationDataset",
        "ConversationTurn",
        "ConversationDistributionType",
        "generate_conversation_dataset",
        "save_conversation_dataset",
        "load_conversation_dataset",
        "get_conversation_generator"
    ])

# Add MCP Client exports if available
if _MCP_CLIENT_AVAILABLE:
    __all__.extend([
        # Core MCP client components
        "MinimalMCPClient",
        "get_mcp_client",
        "search_memories",
        "call_jean_memory",
        "call_jean_memory_tool", 
        "test_mcp_connection",
        
        # MCP types and utilities
        "MCPRequest",
        "MCPResponse",
        "MCPMemoryResult",
        "MCPError",
        "MCPNetworkError",
        "MCPAuthenticationError",
        "MCPTimeoutError",
        "MCPRateLimitError",
        "create_memory_search_request",
        "create_jean_memory_request",
        "parse_mcp_response"
    ])

# Conversation Test Runner (Task 7)
try:
    from .minimal_test_runner import (
        MinimalTestRunner,
        ConversationTestResult,
        run_conversation_test,
        simple_progress_callback
    )
    from .conversation_state import (
        ConversationState,
        ConversationStateManager,
        get_conversation_state_manager
    )
    
    _TEST_RUNNER_AVAILABLE = True
except ImportError as e:
    _TEST_RUNNER_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"Test Runner not available: {e}")

# Add Test Runner exports if available
if _TEST_RUNNER_AVAILABLE:
    __all__.extend([
        # Core test runner components
        "MinimalTestRunner",
        "ConversationTestResult", 
        "run_conversation_test",
        "simple_progress_callback",
        
        # Conversation state management
        "ConversationState",
        "ConversationStateManager",
        "get_conversation_state_manager"
    ])

# Performance Metrics Extraction (Task 8)
try:
    from .log_parser import (
        LogParser,
        AggregatedMetrics,
        parse_log_file,
        parse_log_text
    )
    from .metrics_extractor import (
        MetricsExtractor,
        ExtractedMetric,
        MetricType,
        LogParsingStats
    )
    
    _LOG_PARSER_AVAILABLE = True
except ImportError as e:
    _LOG_PARSER_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"Log Parser not available: {e}")

# Add Log Parser exports if available
if _LOG_PARSER_AVAILABLE:
    __all__.extend([
        # Core log parsing components
        "LogParser",
        "AggregatedMetrics",
        "parse_log_file",
        "parse_log_text",
        
        # Metrics extraction components
        "MetricsExtractor",
        "ExtractedMetric",
        "MetricType",
        "LogParsingStats"
    ])

# Comprehensive Evaluation Reports (Task 9)
try:
    from .report_generator import (
        EvaluationReportGenerator,
        EvaluationReport,
        ReasoningTypeMetrics,
        JudgeAnalysis,
        PerformanceMetrics,
        FailureAnalysis,
        generate_evaluation_report
    )
    
    _REPORT_GENERATOR_AVAILABLE = True
except ImportError as e:
    _REPORT_GENERATOR_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"Report Generator not available: {e}")

# Add Report Generator exports if available
if _REPORT_GENERATOR_AVAILABLE:
    __all__.extend([
        # Core report generation components
        "EvaluationReportGenerator",
        "EvaluationReport",
        "ReasoningTypeMetrics",
        "JudgeAnalysis",
        "PerformanceMetrics",
        "FailureAnalysis",
        "generate_evaluation_report"
    ])