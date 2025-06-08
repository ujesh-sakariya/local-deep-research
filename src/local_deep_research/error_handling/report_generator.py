"""
ErrorReportGenerator - Create user-friendly error reports
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from loguru import logger

from .error_reporter import ErrorReporter, ErrorCategory
from .llm_explainer import LLMExplainer


class ErrorReportGenerator:
    """
    Generates comprehensive, user-friendly error reports
    """
    
    def __init__(self, llm=None):
        """
        Initialize error report generator
        
        Args:
            llm: Optional LLM instance for generating explanations
        """
        self.error_reporter = ErrorReporter()
        self.llm_explainer = LLMExplainer(llm)
    
    def generate_error_report(
        self, 
        error_message: str, 
        query: str,
        partial_results: Optional[Dict[str, Any]] = None,
        search_iterations: int = 0,
        research_id: Optional[int] = None
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
        # Analyze the error
        context = {
            "query": query,
            "search_iterations": search_iterations,
            "research_id": research_id,
            "partial_results": partial_results
        }
        
        if partial_results:
            context.update(partial_results)
        
        error_analysis = self.error_reporter.analyze_error(error_message, context)
        
        # Generate explanation
        explanation = self.llm_explainer.generate_explanation(error_analysis)
        quick_tip = self.llm_explainer.generate_quick_tip(error_analysis["category"])
        
        # Build the simplified report
        report_parts = []
        
        # Header with user-friendly error message and logs reference
        user_friendly_message = self._make_error_user_friendly(error_message)
        category = error_analysis.get("category")
        category_title = error_analysis.get("title", "Error")
        
        report_parts.append(f"# ⚠️ Research Failed")
        report_parts.append(f"\n**Error Type:** {category_title}")
        report_parts.append(f"\n**What happened:** {user_friendly_message}")
        report_parts.append(f"\n*For detailed error information, scroll down to the research logs and select \"Errors\" from the filter.*")
        
        # Skip explanation section for now (too verbose/unhelpful)
        
        # Support links - moved up for better visibility
        report_parts.append(f"\n## 💬 Get Help")
        report_parts.append("We're here to help you get this working:")
        report_parts.append("- **Chat with the community:** [Discord #help-and-support](https://discord.gg/ttcqQeFcJ3)")
        report_parts.append("- **Report bugs:** [GitHub Issues](https://github.com/LearningCircuit/local-deep-research/issues)")
        report_parts.append("- **Join discussions:** [Reddit r/LocalDeepResearch](https://www.reddit.com/r/LocalDeepResearch/) *(checked less frequently)*")
        
        # Show partial results if available (in expandable section)
        if error_analysis.get("has_partial_results"):
            partial_content = self._format_partial_results(partial_results)
            if partial_content:
                report_parts.append(f"\n<details>\n<summary>📊 Partial Results Available</summary>\n\n{partial_content}\n</details>")
        
        # Technical error (collapsed)
        if user_friendly_message != error_message:
            report_parts.append(f"\n<details>\n<summary>🔧 Technical Details</summary>\n\n**Original Error:**\n```\n{error_message}\n```\n</details>")
        
        return "\n".join(report_parts)
    
    def _format_partial_results(self, partial_results: Optional[Dict[str, Any]]) -> str:
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
                formatted_parts.append(knowledge[:1000] + "..." if len(knowledge) > 1000 else knowledge)
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
                        formatted_parts.append(content[:500] + "..." if len(content) > 500 else content)
                        formatted_parts.append("")
        
        if formatted_parts:
            formatted_parts.append("*Note: The above results were successfully collected before the error occurred.*")
        
        return "\n".join(formatted_parts) if formatted_parts else ""
    
    def _extract_stack_trace(self, error_message: str) -> Optional[str]:
        """
        Extract stack trace from error message if present
        
        Args:
            error_message: The error message
            
        Returns:
            str: Stack trace if found, None otherwise
        """
        # Look for common stack trace patterns
        lines = error_message.split('\n')
        stack_lines = []
        in_stack = False
        
        for line in lines:
            # Common stack trace indicators
            if any(indicator in line.lower() for indicator in [
                'traceback', 'stack trace', 'at ', 'file "', 
                'line ', 'error:', 'exception:', 'caused by:'
            ]):
                in_stack = True
                stack_lines.append(line)
            elif in_stack and line.strip():
                # Continue collecting stack trace lines
                if line.startswith('  ') or 'at ' in line or 'File "' in line:
                    stack_lines.append(line)
                elif not line.strip():
                    # Empty line might still be part of stack
                    stack_lines.append(line)
                else:
                    # Looks like end of stack trace
                    break
        
        # Return stack trace if we found a substantial one
        if len(stack_lines) > 1:
            return '\n'.join(stack_lines)
        
        return None
    
    def _get_technical_context(self, error_analysis: Dict[str, Any], partial_results: Optional[Dict[str, Any]]) -> str:
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
                context_parts.append(f"- **Start Time:** {partial_results['start_time']}")
            
            if "last_activity" in partial_results:
                context_parts.append(f"- **Last Activity:** {partial_results['last_activity']}")
            
            # Add model information
            if "model_config" in partial_results:
                config = partial_results["model_config"]
                context_parts.append(f"- **Model:** {config.get('model_name', 'Unknown')}")
                context_parts.append(f"- **Provider:** {config.get('provider', 'Unknown')}")
            
            # Add search information
            if "search_config" in partial_results:
                search_config = partial_results["search_config"]
                context_parts.append(f"- **Search Engine:** {search_config.get('engine', 'Unknown')}")
                context_parts.append(f"- **Max Results:** {search_config.get('max_results', 'Unknown')}")
            
            # Add any error codes or HTTP status
            if "status_code" in partial_results:
                context_parts.append(f"- **Status Code:** {partial_results['status_code']}")
            
            if "error_code" in partial_results:
                context_parts.append(f"- **Error Code:** {partial_results['error_code']}")
        
        # Add error-specific context based on category
        category = error_analysis.get("category")
        if category:
            if "connection" in category.value.lower():
                context_parts.append(f"- **Network Error:** Connection-related issue detected")
                context_parts.append(f"- **Retry Recommended:** Check service status and try again")
            elif "model" in category.value.lower():
                context_parts.append(f"- **Model Error:** Issue with AI model or configuration")
                context_parts.append(f"- **Check:** Model service availability and parameters")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _get_research_logs(self, research_id: int) -> Optional[str]:
        """
        Fetch logs from the database for this specific research run
        
        Args:
            research_id: The research ID to fetch logs for
            
        Returns:
            str: Formatted logs or None if no logs found
        """
        try:
            # Import here to avoid circular imports
            from local_deep_research.web.database.models import ResearchLog
            from local_deep_research.web.database.database import get_db_session
            
            with get_db_session() as session:
                # Get all logs for this research, ordered by timestamp
                logs = session.query(ResearchLog).filter(
                    ResearchLog.research_id == research_id
                ).order_by(ResearchLog.timestamp.asc()).all()
                
                if not logs:
                    return None
                
                # Format logs for display
                log_parts = []
                error_logs = []
                warning_logs = []
                info_logs = []
                
                for log in logs:
                    timestamp = log.timestamp.strftime('%H:%M:%S')
                    location = f"{log.module}:{log.function}:{log.line_no}"
                    
                    # Categorize logs
                    if log.level in ['ERROR', 'CRITICAL']:
                        error_logs.append(f"**{timestamp}** `{log.level}` [{location}]\n```\n{log.message}\n```")
                    elif log.level == 'WARNING':
                        warning_logs.append(f"**{timestamp}** `{log.level}` [{location}] {log.message}")
                    elif log.level in ['INFO', 'MILESTONE']:
                        info_logs.append(f"**{timestamp}** `{log.level}` {log.message}")
                
                # Show errors first (most important)
                if error_logs:
                    log_parts.append("### 🚨 Errors and Exceptions\n")
                    log_parts.extend(error_logs[:5])  # Show last 5 errors
                    if len(error_logs) > 5:
                        log_parts.append(f"\n*({len(error_logs) - 5} more errors - see full logs panel)*")
                    log_parts.append("")
                
                # Then warnings
                if warning_logs:
                    log_parts.append("### ⚠️ Warnings\n")
                    log_parts.extend(warning_logs[-3:])  # Show last 3 warnings
                    if len(warning_logs) > 3:
                        log_parts.append(f"\n*({len(warning_logs) - 3} more warnings - see full logs panel)*")
                    log_parts.append("")
                
                # Finally recent activity (info logs)
                if info_logs:
                    log_parts.append("### ℹ️ Recent Activity\n")
                    log_parts.extend(info_logs[-5:])  # Show last 5 info logs
                    if len(info_logs) > 5:
                        log_parts.append(f"\n*({len(info_logs) - 5} more info logs - see full logs panel)*")
                
                # Add summary
                total_logs = len(logs)
                log_parts.append(f"\n**Total logs for this research:** {total_logs}")
                log_parts.append(f"**Errors:** {len(error_logs)} | **Warnings:** {len(warning_logs)} | **Info:** {len(info_logs)}")
                
                return "\n".join(log_parts) if log_parts else None
                
        except Exception as e:
            logger.warning(f"Could not fetch research logs for ID {research_id}: {e}")
            return f"*Could not fetch logs from database: {str(e)}*"
    
    def generate_quick_error_summary(self, error_message: str) -> Dict[str, str]:
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
            "quick_fix": self.llm_explainer.generate_quick_tip(error_analysis["category"]),
            "recoverable": error_analysis["recoverable"]
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
            )
        }
        
        # Check each pattern and replace if found
        for pattern, replacement in error_replacements.items():
            import re
            if re.search(pattern, error_message, re.IGNORECASE):
                return f"{replacement}\n\nTechnical error: {error_message}"
        
        # If no specific replacement found, return original message
        return error_message