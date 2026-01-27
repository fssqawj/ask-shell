"""LLM 客户端基类"""

from abc import ABC, abstractmethod
from typing import Optional, List

from ..models.types import LLMResponse, ExecutionResult, Message


class BaseLLMClient(ABC):
    """LLM 客户端基类"""
    
    SYSTEM_PROMPT = """你是一个专业的 Shell 命令生成助手。用户会给你描述一个任务，你需要生成合适的 shell 命令来完成这个任务。

你的回复必须是一个 JSON 对象，格式如下：
{
    "thinking": "你对任务的分析和思考过程",
    "command": "要执行的 shell 命令（每次只生成一条）",
    "explanation": "对命令的简要解释",
    "is_complete": false,
    "next_step": "下一步计划（如果任务还未完成）",
    "error_analysis": "如果上一条命令执行失败，分析失败原因",
    "is_dangerous": false,
    "danger_reason": "如果是危险操作，说明原因"
}

重要规则：
1. 每次只生成一条命令，不要一次性生成多条
2. 命令必须是可以直接在 bash/zsh 中执行的
3. 如果任务已经完成，将 is_complete 设为 true，command 可以为空
4. 如果需要多步操作，每次只执行一步，根据执行结果决定下一步
5. 每次命令执行后的输出会反馈给你，请根据输出调整后续命令
6. 如果命令执行失败，请分析原因并尝试修复
7. 如果连续多次失败，请尝试不同的方法
8. 始终关注最终目标，确保任务真正完成

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
        self.messages: List[Message] = []
    
    def reset(self):
        """重置对话历史"""
        self.messages = []
    
    def _build_result_message(self, result: ExecutionResult) -> str:
        """构建执行结果消息"""
        status = "成功" if result.success else "失败"
        return f"""上一条命令执行{status}：
命令: {result.command}
返回码: {result.returncode}
输出:
{result.truncated_output()}

请根据执行结果决定下一步操作。如果任务已完成，设置 is_complete 为 true。"""

    def _build_task_message(self, task: str) -> str:
        """构建任务消息"""
        return f"请帮我完成以下任务: {task}"
    
    @abstractmethod
    def generate(self, user_input: str, last_result: Optional[ExecutionResult] = None) -> LLMResponse:
        """
        生成下一步命令
        
        Args:
            user_input: 用户输入的任务描述
            last_result: 上一次命令执行的结果
            
        Returns:
            LLMResponse: LLM 响应
        """
        pass
