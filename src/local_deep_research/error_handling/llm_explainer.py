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
        self.explanation_templates = {
            ErrorCategory.CONNECTION_ERROR: """
                You encountered a connection problem while the system was trying to communicate with your AI model service. 
                This typically happens when the model service (like Ollama or LM Studio) isn't running or isn't accessible.
                
                The good news is this is usually easy to fix by checking that your AI service is properly started.
            """,
            ErrorCategory.MODEL_ERROR: """
                There was an issue with the AI model configuration. This could mean the model you selected 
                isn't available, or there's a problem with your API credentials.
                
                You can often resolve this by checking your model settings or trying a different model.
            """,
            ErrorCategory.SEARCH_ERROR: """
                The system had trouble searching for information. This might be due to internet connectivity 
                issues or problems with the search service.
                
                Your research can usually be retried once the connection is restored.
            """,
            ErrorCategory.SYNTHESIS_ERROR: """
                The research data was successfully collected, but there was an issue generating the final report. 
                This often happens due to temporary model connectivity issues.
                
                The partial research results are still available and useful, even though the final synthesis failed.
            """,
            ErrorCategory.FILE_ERROR: """
                There was a problem saving the research results to your computer. This could be due to 
                insufficient permissions or disk space.
                
                Your research data is still available, but the file couldn't be written.
            """,
            ErrorCategory.UNKNOWN_ERROR: """
                An unexpected error occurred during your research. While this is frustrating, 
                the detailed logs can help identify what went wrong.
                
                This type of error helps improve the system when reported.
            """
        }
    
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
        
        # Priority 2: Try LLM for unknown/complex errors
        if self.llm:
            try:
                llm_explanation = self._generate_llm_explanation(category, original_error, context)
                if llm_explanation:
                    return llm_explanation
            except Exception as e:
                logger.warning(f"Failed to generate LLM explanation: {e}")
        
        # Priority 3: Simple fallback
        return "An unexpected error occurred during your research. Check the technical details below for more information."
    
    def _generate_llm_explanation(self, category: ErrorCategory, error_message: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Use LLM to generate explanation
        
        Args:
            category: Error category
            error_message: Original error message
            context: Error context
            
        Returns:
            Optional[str]: LLM-generated explanation
        """
        try:
            # Prepare prompt for LLM with category context
            category_hint = ""
            if category:
                category_hints = {
                    ErrorCategory.CONNECTION_ERROR: "This appears to be a connection or network issue with the AI service",
                    ErrorCategory.MODEL_ERROR: "This seems to be related to AI model configuration or availability", 
                    ErrorCategory.SEARCH_ERROR: "This looks like an issue with the search functionality",
                    ErrorCategory.SYNTHESIS_ERROR: "This appears to be a problem during report generation",
                    ErrorCategory.FILE_ERROR: "This seems to be a file system or permissions issue",
                    ErrorCategory.UNKNOWN_ERROR: "This is an unexpected error that needs analysis"
                }
                category_hint = category_hints.get(category, "")
            
            prompt = f"""
You are helping a user understand what went wrong with their research process. 
Please provide a brief, friendly, and helpful explanation of this error.

Error Type: {category_hint}
Technical Error: {error_message}
Research Context: {context}

Please explain:
1. What happened in simple terms
2. Why this might have occurred  
3. That partial results may still be available if applicable
4. Reassurance that this can usually be fixed

Keep it concise, helpful, and friendly. Avoid technical jargon.
"""
            
            response = self.llm.invoke(prompt)
            return str(response.content) if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.warning(f"LLM explanation generation failed: {e}")
            return None
    
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
    
    def generate_quick_tip(self, category: ErrorCategory) -> str:
        """
        Generate a quick tip for the error category
        
        Args:
            category: Error category
            
        Returns:
            str: Quick tip
        """
        tips = {
            ErrorCategory.CONNECTION_ERROR: "💡 **Quick Fix:** Check if your AI service (Ollama/LM Studio) is running",
            ErrorCategory.MODEL_ERROR: "💡 **Quick Fix:** Try switching to a different model in settings",
            ErrorCategory.SEARCH_ERROR: "💡 **Quick Fix:** Check your internet connection and try again", 
            ErrorCategory.SYNTHESIS_ERROR: "💡 **Good News:** Your research data was collected successfully",
            ErrorCategory.FILE_ERROR: "💡 **Quick Fix:** Check available disk space and file permissions",
            ErrorCategory.UNKNOWN_ERROR: "💡 **Next Step:** Check the detailed logs below for more information",
        }
        return tips.get(category, "💡 **Tip:** Try running the research again or check the logs for details")