"""
LLMExplainer - Generate helpful error explanations using LLM
"""

from typing import Optional, Dict, Any
from loguru import logger
from .error_reporter import ErrorCategory


class LLMExplainer:
    """
    Uses LLM to generate helpful explanations for errors
    """
    
    def __init__(self, llm=None):
        """
        Initialize LLM explainer
        
        Args:
            llm: Optional LLM instance to use for explanations
        """
        self.llm = llm
    
    def generate_explanation(self, error_analysis: Dict[str, Any]) -> str:
        """
        Generate a helpful explanation for an error - Priority: specific patterns -> LLM -> category templates
        
        Args:
            error_analysis: Error analysis from ErrorReporter
            
        Returns:
            str: Human-friendly explanation
        """
        category = error_analysis.get("category")
        original_error = error_analysis.get("original_error", "")
        context = error_analysis.get("context", {})
        
        # Priority 1: Check for specific known error patterns first
        specific_explanation = self._get_specific_error_explanation(original_error)
        if specific_explanation:
            return specific_explanation
        
        # Priority 2: Simple fallback (LLM explanation disabled for now)
        return "An unexpected error occurred during your research. Check the technical details below for more information."
    
    # LLM explanation functionality removed - was too verbose and unhelpful
    
    def _get_template_explanation(self, category: ErrorCategory, error_analysis: Dict[str, Any]) -> str:
        """
        Get template-based explanation as fallback
        
        Args:
            category: Error category
            error_analysis: Error analysis data
            
        Returns:
            str: Template-based explanation
        """
        base_explanation = self.explanation_templates.get(
            category, 
            self.explanation_templates[ErrorCategory.UNKNOWN_ERROR]
        ).strip()
        
        # Add context-specific information
        has_partial = error_analysis.get("has_partial_results", False)
        if has_partial:
            base_explanation += "\n\n✅ **Good news:** Some research data was successfully collected and is shown below."
        
        return base_explanation
    
    # Quick tips removed - not being used in simplified error reports
    
    def _get_specific_error_explanation(self, error_message: str) -> Optional[str]:
        """
        Get specific explanations for known exact error patterns (Priority 1)
        
        Args:
            error_message: The error message to check
            
        Returns:
            str: Specific explanation if pattern matches, None otherwise
        """
        error_lower = error_message.lower()
        
        # Ollama port switching issue (our current debugging case)
        if "post predict" in error_lower and "eof" in error_lower and "127.0.0.1:" in error_message:
            return """
            **Ollama Port Switching Issue Detected**
            
            Your Ollama service appears to be switching to random ports during operation. This is a known issue where langchain-ollama 
            changes from the configured localhost:11434 to random ports like 127.0.0.1:39841, causing connection failures.
            
            **Quick fixes to try:**
            - Restart your Ollama service: `ollama serve`
            - Restart the LDR application  
            - Check if multiple Ollama instances are running
            - Try switching to a different model provider temporarily
            """.strip()
        
        # API key issues
        if "api key" in error_lower and ("invalid" in error_lower or "unauthorized" in error_lower):
            return """
            **API Key Problem**
            
            Your API key appears to be invalid or missing. This prevents the system from connecting to your AI service.
            
            **How to fix:**
            - Check your API key in the settings
            - Verify the key hasn't expired
            - Make sure you've entered it correctly (no extra spaces)
            """.strip()
        
        # Model not found
        if "model" in error_lower and ("not found" in error_lower or "does not exist" in error_lower):
            return """
            **Model Not Available**
            
            The AI model you selected isn't available on your system.
            
            **How to fix:**
            - Download the model: `ollama pull [model-name]`
            - Check available models: `ollama list`
            - Try switching to a different model in settings
            """.strip()
        
        # Connection refused / service not running
        if "connection refused" in error_lower or "service unavailable" in error_lower:
            return """
            **AI Service Not Running**
            
            The AI service (like Ollama or LM Studio) isn't running or isn't accessible.
            
            **How to fix:**
            - Start Ollama: `ollama serve`
            - Check if LM Studio is running
            - Verify the service URL in settings
            """.strip()
        
        # ThreadPoolExecutor max_workers issue
        if "max_workers must be greater than 0" in error_message:
            return """
            **Threading Configuration Error**
            
            The system tried to create a thread pool with zero workers, which isn't allowed.
            This typically happens when there are no search questions to process.
            
            **Quick fix:**
            - Try running the research again
            - Check your search configuration settings
            - This is usually a temporary issue
            """.strip()
        
        return None