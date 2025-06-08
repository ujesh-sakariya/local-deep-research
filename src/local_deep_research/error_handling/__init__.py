"""
Error Handling Module for Local Deep Research

This module provides comprehensive error handling capabilities including:
- Error categorization and analysis
- LLM-powered error explanations
- User-friendly error report generation
- Integration with partial research results
"""

from .error_reporter import ErrorReporter
from .llm_explainer import LLMExplainer
from .report_generator import ErrorReportGenerator

__all__ = ["ErrorReporter", "LLMExplainer", "ErrorReportGenerator"]