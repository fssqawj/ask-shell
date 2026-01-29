"""LLM Skill - Shell command generation and content processing with LLM"""

from typing import List, Optional, Dict, Any, Callable
from .base_skill import BaseSkill, SkillResponse, SkillCapability
from ..llm.base import BaseLLMClient
from ..llm.openai_client import OpenAIClient
from ..models.types import ExecutionResult


class LLMSkill(BaseSkill):
    """
    LLM-powered skill for command generation and content processing
    
    This skill uses a language model to:
    1. Generate shell commands to accomplish tasks
    2. Process content (translate, summarize, analyze, etc.)
    3. Adapt based on execution results
    """
    
    def __init__(self):
        """
        Initialize LLM skill
        """
        super().__init__()
        self.llm: BaseLLMClient = OpenAIClient()
        self.llm.set_direct_mode(False)  # Default to command mode
    
    def get_capabilities(self) -> List[SkillCapability]:
        """LLM skill provides command generation and LLM processing"""
        return [
            SkillCapability.COMMAND_GENERATION,
            SkillCapability.LLM_PROCESSING
        ]
    
    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> SkillResponse:
        """
        Execute LLM skill to handle the task
        
        Args:
            task: Task description
            context: Execution context including last_result, etc.
            stream_callback: Optional streaming callback for real-time output
            **kwargs: Additional parameters
            
        Returns:
            SkillResponse with LLM's decision
        """
        if context is None:
            context = {}
        
        # Get execution context from context
        last_result = context.get('last_result')
        history = context.get('history', [])
        
        # Call LLM to generate response
        try:
            llm_response = self.llm.generate(task, last_result, stream_callback, history=history)
            
            # Convert LLMResponse to SkillResponse
            return SkillResponse(
                skill_name=self.name,
                thinking=llm_response.thinking,
                is_complete=llm_response.is_complete,
                command=llm_response.command,
                explanation=llm_response.explanation,
                next_step=llm_response.next_step,
                is_dangerous=llm_response.is_dangerous,
                danger_reason=llm_response.danger_reason,
                error_analysis=llm_response.error_analysis,
                direct_response=llm_response.direct_response,
                needs_llm_processing=llm_response.needs_llm_processing
            )
        except Exception as e:
            return SkillResponse(
                skill_name=self.name,
                thinking=f"LLM call failed: {str(e)}",
                is_complete=True,
                direct_response=f"Error: Failed to generate response from LLM: {str(e)}"
            )
    
    def reset(self):
        """Reset LLM conversation state"""
        self.llm.reset()
    
    def get_description(self) -> str:
        """Get skill description"""
        return "通用AI助手，能够生成和执行shell命令，以及处理各种内容任务（翻译、总结、分析等）"
