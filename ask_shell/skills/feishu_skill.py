"""Feishu Automation Skill for macOS - Send messages using AppleScript"""

import subprocess
import json
from typing import List, Optional, Dict, Any, Callable
from .base_skill import BaseSkill, SkillExecutionResponse
from ..skills.utils import build_full_history_message


class FeishuSkill(BaseSkill):
    """
    Feishu automation skill for macOS using AppleScript
    Allows sending messages to contacts in Feishu/Lark
    """

    SYSTEM_PROMPT = """你是一个专业的macOS Lark 自动化助手。用户会给你描述一个 Lark 消息发送任务，你需要生成合适的AppleScript代码来完成这个任务.

你的回复必须是一个 JSON 对象，格式如下：
{
    "thinking": "你对任务的分析和思考过程",
    "command": "要执行的AppleScript命令",
    "explanation": "对命令的简要解释"
}

重要规则：
1. 生成osascript命令来执行 Lark 自动化任务
2. 首先检查 Lark 是否已安装和运行
3. 如果 Lark 未运行，则启动它
4. 如果 Lark 窗口被最小化或隐藏，则将其恢复到前台
5. 搜索指定的联系人或群组（使用 Lark 的搜索功能）
6. 发送消息
7. 处理可能的错误情况（如联系人不存在）
8. 对于中文文本输入，使用剪贴板粘贴方法，避免键盘输入法问题

基本的osascript命令结构：
osascript -e '
tell application "Lark"
    reopen
    activate
end tell

delay 2

-- 打开搜索
tell application "System Events" to keystroke "k" using command down
delay 1

-- 设置联系人名称到剪贴板并粘贴
set the clipboard to "安炜杰的飞书助手"
tell application "System Events" to keystroke "v" using command down
delay 1

-- 选择联系人
tell application "System Events" to keystroke return
delay 1

-- 设置消息内容到剪贴板并粘贴
set the clipboard to "测试消息"
tell application "System Events" to keystroke "v" using command down
delay 0.5

-- 发送消息
tell application "System Events" to keystroke return
'


推荐的操作序列：
1. 启动Feishu/Lark应用- tell application "Lark" to reopen
2. 确保应用窗口可见 - 使用tell application "Lark" to activate
3. 等待应用加载
4. 使用快捷键 ⌘K 打开搜索
5. 通过剪贴板设置联系人名称
6. 通过System Events粘贴联系人名称
7. 按回车选择联系人
8. 通过剪贴板设置消息内容
9. 通过System Events粘贴消息内容
10. 按回车发送消息

AppleScript参考：
- 重新打开窗口: tell application "Lark" to reopen
- 激活应用: tell application "Lark" to activate
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

    def get_capabilities(self) -> List[str]:
        """Feishu skill provides GUI automation capability for Feishu messaging"""
        return [
            "gui_automation"  # GUI automation for Feishu
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

        # Call LLM to generate response with direct parsing
        try:
            from ..models.types import CommandSkillResponse
            # Generate and directly parse into CommandSkillResponse
            user_prompt = build_full_history_message(history, task)
            llm_response = self.llm.generate(self.SYSTEM_PROMPT, user_prompt, stream_callback, response_class=CommandSkillResponse)

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
                        explanation=parsed_data.get("explanation", "")
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
                explanation=parsed_response.explanation
            )
        except Exception as e:
            return SkillExecutionResponse(
                thinking=f"LLM call failed: {str(e)}",
                direct_response=f"Error: Failed to generate Feishu automation from LLM: {str(e)}"
            )

    def reset(self):
        """Reset LLM conversation state"""
        pass

    def get_description(self) -> str:
        """Get skill description"""
        return "Feishu自动化助手：在macOS上通过AppleScript自动化Feishu/Lark桌面应用发送消息"