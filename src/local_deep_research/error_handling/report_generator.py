"""
ErrorReportGenerator - Create user-friendly error reports
"""

from typing import Dict, Any, Optional
from loguru import logger

from .error_reporter import ErrorReporter


class ErrorReportGenerator:
    """
    Generates comprehensive, user-friendly error reports
    """

    def __init__(self, llm=None):
        """
        Initialize error report generator

        Args:
            llm: Optional LLM instance (unused, kept for compatibility)
        """
        self.error_reporter = ErrorReporter()

    def generate_error_report(
        self,
        error_message: str,
        query: str,
        partial_results: Optional[Dict[str, Any]] = None,
        search_iterations: int = 0,
        research_id: Optional[int] = None,
    ) -> str:
        """
        Generate a comprehensive error report

        Args:
            error_message: The error that occurred
            query: The research query
            partial_results: Any partial results that were collected
            search_iterations: Number of search iterations completed
            research_id: Research ID for reference

        Returns:
            str: Formatted error report in Markdown
        """
        try:
            # Analyze the error
            context = {
                "query": query,
                "search_iterations": search_iterations,
                "research_id": research_id,
                "partial_results": partial_results,
            }

            if partial_results:
                context.update(partial_results)

            error_analysis = self.error_reporter.analyze_error(
                error_message, context
            )

            # Build the simplified report
            report_parts = []

            # Header with user-friendly error message and logs reference
            user_friendly_message = self._make_error_user_friendly(
                error_message
            )
            category_title = error_analysis.get("title", "Error")

            report_parts.append("# ⚠️ Research Failed")
            report_parts.append(f"\n**Error Type:** {category_title}")
            report_parts.append(f"\n**What happened:** {user_friendly_message}")
            report_parts.append(
                '\n*For detailed error information, scroll down to the research logs and select "Errors" from the filter.*'
            )

            # Support links - moved up for better visibility
            report_parts.append("\n## 💬 Get Help")
            report_parts.append("We're here to help you get this working:")
            report_parts.append(
                "- **Documentation & guides:** [Wiki](https://github.com/LearningCircuit/local-deep-research/wiki)"
            )
            report_parts.append(
                "- **Chat with the community:** [Discord #help-and-support](https://discord.gg/ttcqQeFcJ3)"
            )
            report_parts.append(
                "- **Report bugs:** [GitHub Issues](https://github.com/LearningCircuit/local-deep-research/issues)"
            )
            report_parts.append(
                "- **Join discussions:** [Reddit r/LocalDeepResearch](https://www.reddit.com/r/LocalDeepResearch/) *(checked less frequently)*"
            )

            # Show partial results if available (in expandable section)
            if error_analysis.get("has_partial_results"):
                partial_content = self._format_partial_results(partial_results)
                if partial_content:
                    report_parts.append(
                        f"\n<details>\n<summary>📊 Partial Results Available</summary>\n\n{partial_content}\n</details>"
                    )

            return "\n".join(report_parts)

        except Exception as e:
            # Fallback: always return something, even if error report generation fails
            logger.exception(f"Failed to generate error report: {e}")
            return f"""# ⚠️ Research Failed

**What happened:** {error_message}

## 💬 Get Help
We're here to help you get this working:
- **Documentation & guides:** [Wiki](https://github.com/LearningCircuit/local-deep-research/wiki)
- **Chat with the community:** [Discord #help-and-support](https://discord.gg/ttcqQeFcJ3)
- **Report bugs:** [GitHub Issues](https://github.com/LearningCircuit/local-deep-research/issues)

*Note: Error report generation failed - showing basic error information.*"""

    def _format_partial_results(
        self, partial_results: Optional[Dict[str, Any]]
    ) -> str:
        """
        Format partial results for display

        Args:
            partial_results: Partial results data

        Returns:
            str: Formatted partial results
        """
        if not partial_results:
            return ""

        formatted_parts = []

        # Current knowledge summary
        if "current_knowledge" in partial_results:
            knowledge = partial_results["current_knowledge"]
            if knowledge and len(knowledge.strip()) > 50:
                formatted_parts.append("### Research Summary\n")
                formatted_parts.append(
                    knowledge[:1000] + "..."
                    if len(knowledge) > 1000
                    else knowledge
                )
                formatted_parts.append("")

        # Search results
        if "search_results" in partial_results:
            results = partial_results["search_results"]
            if results:
                formatted_parts.append("### Search Results Found\n")
                for i, result in enumerate(results[:5], 1):  # Show top 5
                    title = result.get("title", "Untitled")
                    url = result.get("url", "")
                    formatted_parts.append(f"{i}. **{title}**")
                    if url:
                        formatted_parts.append(f"   - URL: {url}")
                formatted_parts.append("")

        # Findings
        if "findings" in partial_results:
            findings = partial_results["findings"]
            if findings:
                formatted_parts.append("### Research Findings\n")
                for i, finding in enumerate(findings[:3], 1):  # Show top 3
                    content = finding.get("content", "")
                    if content and not content.startswith("Error:"):
                        phase = finding.get("phase", f"Finding {i}")
                        formatted_parts.append(f"**{phase}:**")
                        formatted_parts.append(
                            content[:500] + "..."
                            if len(content) > 500
                            else content
                        )
                        formatted_parts.append("")

        if formatted_parts:
            formatted_parts.append(
                "*Note: The above results were successfully collected before the error occurred.*"
            )

        return "\n".join(formatted_parts) if formatted_parts else ""

    def _get_technical_context(
        self,
        error_analysis: Dict[str, Any],
        partial_results: Optional[Dict[str, Any]],
    ) -> str:
        """
        Get additional technical context for the error

        Args:
            error_analysis: Error analysis results
            partial_results: Partial results if available

        Returns:
            str: Technical context information
        """
        context_parts = []

        # Add timing information if available
        if partial_results:
            if "start_time" in partial_results:
                context_parts.append(
                    f"- **Start Time:** {partial_results['start_time']}"
                )

            if "last_activity" in partial_results:
                context_parts.append(
                    f"- **Last Activity:** {partial_results['last_activity']}"
                )

            # Add model information
            if "model_config" in partial_results:
                config = partial_results["model_config"]
                context_parts.append(
                    f"- **Model:** {config.get('model_name', 'Unknown')}"
                )
                context_parts.append(
                    f"- **Provider:** {config.get('provider', 'Unknown')}"
                )

            # Add search information
            if "search_config" in partial_results:
                search_config = partial_results["search_config"]
                context_parts.append(
                    f"- **Search Engine:** {search_config.get('engine', 'Unknown')}"
                )
                context_parts.append(
                    f"- **Max Results:** {search_config.get('max_results', 'Unknown')}"
                )

            # Add any error codes or HTTP status
            if "status_code" in partial_results:
                context_parts.append(
                    f"- **Status Code:** {partial_results['status_code']}"
                )

            if "error_code" in partial_results:
                context_parts.append(
                    f"- **Error Code:** {partial_results['error_code']}"
                )

        # Add error-specific context based on category
        category = error_analysis.get("category")
        if category:
            if "connection" in category.value.lower():
                context_parts.append(
                    "- **Network Error:** Connection-related issue detected"
                )
                context_parts.append(
                    "- **Retry Recommended:** Check service status and try again"
                )
            elif "model" in category.value.lower():
                context_parts.append(
                    "- **Model Error:** Issue with AI model or configuration"
                )
                context_parts.append(
                    "- **Check:** Model service availability and parameters"
                )

        return "\n".join(context_parts) if context_parts else ""

    def generate_quick_error_summary(
        self, error_message: str
    ) -> Dict[str, str]:
        """
        Generate a quick error summary for API responses

        Args:
            error_message: The error message

        Returns:
            dict: Quick error summary
        """
        error_analysis = self.error_reporter.analyze_error(error_message)

        return {
            "title": error_analysis["title"],
            "category": error_analysis["category"].value,
            "severity": error_analysis["severity"],
            "recoverable": error_analysis["recoverable"],
        }

    def _make_error_user_friendly(self, error_message: str) -> str:
        """
        Replace cryptic technical error messages with user-friendly versions

        Args:
            error_message: The original technical error message

        Returns:
            str: User-friendly error message, or original if no replacement found
        """
        # Dictionary of technical errors to user-friendly messages
        error_replacements = {
            "max_workers must be greater than 0": (
                "This is typically an issue with the LLM not being available."
            ),
            "POST predict.*EOF": (
                "Lost connection to Ollama. This usually means Ollama stopped responding or there's a network issue. Try restarting Ollama or checking if it's still running."
            ),
        }

        # Check each pattern and replace if found
        for pattern, replacement in error_replacements.items():
            import re

            if re.search(pattern, error_message, re.IGNORECASE):
                return f"{replacement}\n\nTechnical error: {error_message}"

        # If no specific replacement found, return original message
        return error_message
