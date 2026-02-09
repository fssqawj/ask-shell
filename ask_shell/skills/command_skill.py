"""Command Generation Skill - Generate shell commands with LLM"""

import json
from typing import List, Optional, Dict, Any, Callable

from loguru import logger
from .base_skill import BaseSkill, SkillExecutionResponse
from ..llm.base import BaseLLMClient
from ..llm.openai_client import OpenAIClient
from ..skills.utils import build_full_history_message


class CommandSkill(BaseSkill):
    """
    Command generation skill using LLM to create and execute shell commands
    """
    
    SYSTEM_PROMPT = """你是一个专业的 Shell 命令生成助手。用户会给你描述一个任务，你需要生成合适的 shell 命令来完成这个任务。

你的回复必须是一个 JSON 对象，格式如下：
{
    "thinking": "你对任务的分析和思考过程",
    "command": "要执行的 shell 命令（每次只生成一条）",
    "explanation": "对命令的简要解释",
    "next_step": "下一步计划（如果任务还未完成）",
    "error_analysis": "如果上一条命令执行失败，分析失败原因",
    "is_dangerous": false,
    "danger_reason": "如果是危险操作，说明原因"
}

重要规则：
1. 每次只生成一条命令，不要一次性生成多条
2. 命令必须是可以直接在 bash/zsh 中执行的
3. 不再设置 task_complete（由 skill selector 决定任务是否完成）
4. 如果需要多步操作，每次只执行一步，根据执行结果决定下一步
5. 每次命令执行后的输出会反馈给你，请根据输出调整后续命令
6. 如果命令执行失败，请分析原因并尝试修复
7. 如果连续多次失败，请尝试不同的方法
8. 始终关注最终目标，确保任务真正完成

**智能处理模式：**
当任务需要AI能力（翻译、总结、分析等）时，你应该：
1. 先执行必要的命令获取数据（如 curl 获取网页、cat 读取文件）
2. 如果需要对命令输出进行内容处理（如翻译、总结、分析），应该让技能选择器选择DirectLLMSkill来处理


示例场景：
- 任务："翻译网页 http://example.com 的内容"
  步骤1: {"command": "curl -s http://example.com", "explanation": "获取网页内容"}
  步骤2: {"command": "", "explanation": "等待技能选择器选择DirectLLMSkill进行翻译"}

- 任务："总结README.md文件"
  步骤1: {"command": "cat README.md", "explanation": "读取文件内容"}
  步骤2: {"command": "", "explanation": "等待技能选择器选择DirectLLMSkill进行总结"}

危险操作判断（is_dangerous 设为 true 的情况）：
- 删除文件或目录的命令（rm、rmdir）
- 修改系统配置文件（/etc/ 下的文件）
- 修改权限的命令（chmod、chown）
- 涉及 sudo 或需要 root 权限的操作
- 可能覆盖现有文件的重定向操作（>）
- 批量操作（如 find ... -exec rm）
- 网络相关的敏感操作
- 任何不可逆的操作

对于安全的操作（如 ls、cat、echo、mkdir、创建新文件等），is_dangerous 设为 false。"""

    def __init__(self):
        """
        Initialize command skill
        """
        super().__init__()
        self.llm: BaseLLMClient = OpenAIClient()
    
    def get_capabilities(self) -> List[str]:
        """Command skill provides command generation capability"""
        return [
            "command_generation"
        ]
    
    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> SkillExecutionResponse:
        """
        Execute command skill to generate shell commands for the task
            
        Args:
            task: Task description
            context: Execution context including last_result, etc.
            stream_callback: Optional streaming callback for real-time output
            **kwargs: Additional parameters including selection_reasoning
            
        Returns:
            SkillExecutionResponse with command generation result
        """
        if context is None:
            context = {}
            
        # Get execution context from context
        last_result = context.get('last_result')
        history = context.get('history', [])
            
        # Get the reasoning for why this skill was selected (though command skill doesn't modify its behavior based on this)
        selection_reasoning = kwargs.get('selection_reasoning', '')
            
        # Build hints information
        hints_info = self._build_hints_info()
            
        # Call LLM to generate response with direct parsing using CommandSkillResponse dataclass
        try:
            from ..models.types import CommandSkillResponse
            # Generate and directly parse into CommandSkillResponse
            user_prompt = build_full_history_message(history, task)
            
            # Add hints to user prompt if available
            if hints_info:
                user_prompt = f"{user_prompt}\n\n{hints_info}"
            logger.info(f"Command Skill LLM USER Prompt: {user_prompt}")
            llm_response = self.llm.generate(self.SYSTEM_PROMPT, user_prompt, stream_callback, response_class=CommandSkillResponse)
            
            return SkillExecutionResponse(
                thinking=llm_response.thinking,
                command=llm_response.command,
                explanation=llm_response.explanation,
                next_step=llm_response.next_step,
                is_dangerous=llm_response.is_dangerous,
                danger_reason=llm_response.danger_reason,
                error_analysis=llm_response.error_analysis,
                # Don't set task_complete here - skill selector will decide
            )
        except Exception as e:
            return SkillExecutionResponse(
                thinking=f"LLM call failed: {str(e)}",
                direct_response=f"Error: Failed to generate command from LLM: {str(e)}"
            )
    
    def reset(self):
        """Reset LLM conversation state"""
        pass

    def get_description(self) -> str:
        """Get skill description"""
        return "命令生成AI助手，专门生成和执行shell命令来完成任务"