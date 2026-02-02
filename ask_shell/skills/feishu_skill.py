"""Feishu Automation Skill for macOS - Send messages using AppleScript"""

import subprocess
import json
from typing import List, Optional, Dict, Any, Callable
from .base_skill import BaseSkill, SkillExecutionResponse, SkillCapability


class FeishuSkill(BaseSkill):
    """
    Feishu automation skill for macOS using AppleScript
    Allows sending messages to contacts in Feishu/Lark
    """

    SYSTEM_PROMPT = """你是一个专业的macOS Feishu/Lark自动化助手。用户会给你描述一个Feishu/Lark消息发送任务，你需要生成合适的AppleScript代码来完成这个任务。

你的回复必须是一个 JSON 对象，格式如下：
{
    "thinking": "你对任务的分析和思考过程",
    "command": "要执行的AppleScript命令",
    "explanation": "对命令的简要解释",
    "next_step": "下一步计划（如果任务还未完成）",
    "error_analysis": "如果上一条命令执行失败，分析失败原因",
    "is_dangerous": false,
    "danger_reason": "如果是危险操作，说明原因",
    "direct_response": "当需要AI直接处理内容时填写（如翻译、总结、分析命令输出等）"
}

重要规则：
1. 生成osascript命令来执行Feishu自动化任务
2. 首先检查Feishu是否已安装和运行
3. 如果Feishu未运行，则启动它
4. 搜索指定的联系人或群组
5. 发送消息
6. 处理可能的错误情况（如联系人不存在）
7. 对于中文文本输入，使用剪贴板粘贴方法，避免键盘输入法问题

基本的osascript命令结构：
osascript -e 'tell application "Lark" to activate' -e 'delay 2' -e 'tell application "System Events" to tell process "Lark" to ...'

或者如果是Feishu：
osascript -e 'tell application "Feishu" to activate' -e 'delay 2' -e 'tell application "System Events" to tell process "Feishu" to ...'

推荐的操作序列（解决中文输入问题）：
1. 启动Feishu/Lark应用（根据实际安装的应用名称）
2. 等待应用加载
3. 使用快捷键 ⌘K 打开搜索
4. 通过剪贴板设置联系人名称
5. 通过System Events粘贴联系人名称
6. 按回车选择联系人
7. 通过剪贴板设置消息内容
8. 通过System Events粘贴消息内容
9. 按回车发送消息

AppleScript参考：
- 激活应用: tell application "Lark" to activate 或 tell application "Feishu" to activate
- 延迟: delay 2
- 与UI元素交互: click button "按钮名" 或 set value of text field 1 to "值"
- 键盘快捷键: keystroke "k" using command down
- 剪贴板操作: set the clipboard to "文本内容"
- 粘贴操作: keystroke "v" using command down
- 回车键: keystroke return

中文输入解决方案：
对于包含中文的内容，使用以下方法避免输入法问题：
1. 先将内容复制到剪贴板: set the clipboard to "联系人名称" 或 "消息内容"
2. 然后使用粘贴操作: keystroke "v" using command down

注意：UI元素的具体名称可能会因Feishu/Lark版本不同而略有差异，应用名称也可能是"Lark"或"Feishu"。"""

    def __init__(self):
        """
        Initialize Feishu skill
        """
        super().__init__()
        # Import LLM client
        from ..llm.openai_client import OpenAIClient
        self.llm = OpenAIClient()
        # Set the system prompt for Feishu automation
        self.llm.set_system_prompt(self.SYSTEM_PROMPT)
        self.llm.set_direct_mode(False)  # Set to command mode

    def get_capabilities(self) -> List[SkillCapability]:
        """Feishu skill provides GUI automation capability for Feishu messaging"""
        return [
            SkillCapability.GUI_AUTOMATION  # GUI automation for Feishu
        ]

    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> SkillExecutionResponse:
        """
        Execute Feishu automation skill to send messages

        Args:
            task: Task description (e.g., "给张三发消息：你好")
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

        # Get the reasoning for why this skill was selected
        selection_reasoning = kwargs.get('selection_reasoning', '')

        # Set LLM to command mode
        self.llm.set_direct_mode(False)

        # Call LLM to generate response with direct parsing
        try:
            from ..models.types import CommandSkillResponse
            # Generate and directly parse into CommandSkillResponse
            llm_response = self.llm.generate(task, last_result, stream_callback, history=history, response_class=CommandSkillResponse)

            # If the response is already parsed (when response_class is provided), use it directly
            if hasattr(llm_response, 'command'):  # It's already a CommandSkillResponse object
                parsed_response = llm_response
            else:
                # Fallback to raw JSON parsing if needed
                import json
                try:
                    parsed_data = json.loads(llm_response.raw_json)
                    # Create CommandSkillResponse manually
                    parsed_response = CommandSkillResponse(
                        thinking=parsed_data.get("thinking", ""),
                        command=parsed_data.get("command", ""),
                        explanation=parsed_data.get("explanation", ""),
                        next_step=parsed_data.get("next_step", ""),
                        error_analysis=parsed_data.get("error_analysis", ""),
                        is_dangerous=parsed_data.get("is_dangerous", False),
                        danger_reason=parsed_data.get("danger_reason", ""),
                        direct_response=parsed_data.get("direct_response", "")
                    )
                except json.JSONDecodeError:
                    return SkillExecutionResponse(
                        thinking="Failed to parse LLM response as JSON",
                        direct_response=f"Error: Invalid JSON response from LLM: {llm_response.raw_json if hasattr(llm_response, 'raw_json') else str(llm_response)}"
                    )

            # Convert to SkillExecutionResponse
            # Individual skills no longer decide task completion - that's handled by the skill selector
            return SkillExecutionResponse(
                thinking=parsed_response.thinking,
                command=parsed_response.command,
                explanation=parsed_response.explanation,
                next_step=parsed_response.next_step,
                is_dangerous=parsed_response.is_dangerous,
                danger_reason=parsed_response.danger_reason,
                error_analysis=parsed_response.error_analysis,
                # Don't set task_complete here - skill selector will decide
            )
        except Exception as e:
            return SkillExecutionResponse(
                thinking=f"LLM call failed: {str(e)}",
                direct_response=f"Error: Failed to generate Feishu automation from LLM: {str(e)}"
            )

    def reset(self):
        """Reset LLM conversation state"""
        self.llm.reset()

    def get_description(self) -> str:
        """Get skill description"""
        return "Feishu自动化助手：在macOS上通过AppleScript自动化Feishu/Lark桌面应用发送消息"