"""Direct LLM Processing Skill - Direct content processing with LLM"""

import json
from typing import List, Optional, Dict, Any, Callable
from .base_skill import BaseSkill, SkillExecutionResponse, SkillCapability
from ..llm.base import BaseLLMClient
from ..llm.openai_client import OpenAIClient


class DirectLLMSkill(BaseSkill):
    """
    Direct LLM processing skill for content processing tasks
    """
    
    SYSTEM_PROMPT = """你是一个强大的 AI 助手，可以帮助用户完成各种任务，比如翻译、总结、分析等。

用户会给你描述一个任务，以及之前任务执行的各个步骤，请你根据当前信息完成任务。
如果不能完成任务，也请在 direct_response 字段中描述原因。

你的回复必须是一个 JSON 对象，格式如下：
{
    "thinking": "你对任务的分析和思考过程",
    "direct_response": "对任务的直接响应内容",
}

重要规则：
1. 如果当前信息足够，直接执行用户要求的任务
2. 提供清晰、准确、有用的回答"""

    def __init__(self):
        """
        Initialize direct LLM skill
        """
        super().__init__()
        self.llm: BaseLLMClient = OpenAIClient()
        # Set the system prompt for direct mode
        self.llm.set_system_prompt(self.SYSTEM_PROMPT)
        self.llm.set_direct_mode(True)  # Set to direct mode
    
    def get_capabilities(self) -> List[SkillCapability]:
        """Direct LLM skill provides LLM processing capability"""
        return [
            SkillCapability.LLM_PROCESSING
        ]
    
    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> SkillExecutionResponse:
        """
        Execute direct LLM skill to process content for the task
            
        Args:
            task: Task description
            context: Execution context including last_result, etc.
            stream_callback: Optional streaming callback for real-time output
            **kwargs: Additional parameters including selection_reasoning
            
        Returns:
            SkillExecutionResponse with direct LLM processing result
        """
        if context is None:
            context = {}
            
        # Get execution context from context
        last_result = context.get('last_result')
        history = context.get('history', [])
            
        # Get the reasoning for why this skill was selected
        selection_reasoning = kwargs.get('selection_reasoning', '')
                
        # Create the enhanced prompt by adding the selection reasoning to the system prompt
        # Add the selection reasoning to the original prompt
        enhanced_prompt = self.SYSTEM_PROMPT
        if selection_reasoning:
            # Append the selection reasoning to the existing prompt
            enhanced_prompt += f"\n\n**技能选择背景**:\n技能选择器选择了你（DirectLLMSkill）来处理这个任务，理由是：{selection_reasoning}"
        
        # Ensure the prompt contains the word 'json' in lowercase to meet OpenAI API requirements
        # The API requires 'json' to be present when using response_format='json_object'
        # Adding a note that contains the word 'json' to satisfy the API validation
        enhanced_prompt += "\n\n(Note: json format required)"
        
        # Set the enhanced prompt for this execution
        self.llm.set_system_prompt(enhanced_prompt)
            
        # Set LLM to direct mode
        self.llm.set_direct_mode(True)
            
        # Call LLM to generate response with direct parsing using DirectLLMSkillResponse dataclass
        try:
            from ..models.types import DirectLLMSkillResponse
            # Generate and directly parse into DirectLLMSkillResponse
            llm_response = self.llm.generate(task, last_result, stream_callback, history=history, response_class=DirectLLMSkillResponse)
            
            # If the response is already parsed (when response_class is provided), use it directly
            if hasattr(llm_response, 'direct_response'):  # It's already a DirectLLMSkillResponse object
                parsed_response = llm_response
            else:
                # Fallback to raw JSON parsing if needed
                import json
                try:
                    parsed_data = json.loads(llm_response.raw_json)
                    # Create DirectLLMSkillResponse manually
                    parsed_response = DirectLLMSkillResponse(
                        thinking=parsed_data.get("thinking", ""),
                        direct_response=parsed_data.get("direct_response", "")
                    )
                except json.JSONDecodeError:
                    return SkillExecutionResponse(
                        thinking="Failed to parse LLM response as JSON",
                        direct_response=f"Error: Invalid JSON response from LLM: {llm_response.raw_json if hasattr(llm_response, 'raw_json') else str(llm_response)}"
                    )
            
            # Convert LLMResponse to SkillExecutionResponse
            # Individual skills no longer decide task completion - that's handled by the skill selector
            return SkillExecutionResponse(
                thinking=parsed_response.thinking,
                direct_response=parsed_response.direct_response,
                # Don't set task_complete here - skill selector will decide
            )
        except Exception as e:
            print(f"LLM call failed: {str(e)}")
            return SkillExecutionResponse(
                thinking=f"LLM call failed: {str(e)}",
                direct_response=f"Error: Failed to process content with LLM: {str(e)}"
            )
    
    def reset(self):
        """Reset LLM conversation state"""
        self.llm.reset()
    
    def get_description(self) -> str:
        """Get skill description"""
        return "直接处理AI助手，专门处理内容任务（翻译、总结、分析等），输入是之前技能的输出的有效文本信息并生成处理后的文本信息"