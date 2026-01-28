"""LLM 客户端基类"""

from abc import ABC, abstractmethod
from typing import Optional, List, Callable

from ..models.types import LLMResponse, ExecutionResult, Message


class BaseLLMClient(ABC):
    """LLM 客户端基类"""
    
    SYSTEM_PROMPT_COMMAND_MODE = """你是一个专业的 Shell 命令生成助手。用户会给你描述一个任务，你需要生成合适的 shell 命令来完成这个任务。

你的回复必须是一个 JSON 对象，格式如下：
{
    "thinking": "你对任务的分析和思考过程",
    "command": "要执行的 shell 命令（每次只生成一条）",
    "explanation": "对命令的简要解释",
    "is_complete": false,
    "next_step": "下一步计划（如果任务还未完成）",
    "error_analysis": "如果上一条命令执行失败，分析失败原因",
    "is_dangerous": false,
    "danger_reason": "如果是危险操作，说明原因",
    "direct_response": "当需要AI直接处理内容时填写（如翻译、总结、分析命令输出等）",
    "needs_llm_processing": false
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

**智能处理模式：**
当任务需要AI能力（翻译、总结、分析等）时，你应该：
1. 先执行必要的命令获取数据（如 curl 获取网页、cat 读取文件）
2. 当命令执行成功并获得数据后，下一步：
   - 设置 needs_llm_processing = true
   - 在 direct_response 中直接处理上一步命令的输出（翻译、总结、分析等）
   - command 留空或设置为空字符串
   - 设置 is_complete = true（如果这是最后一步）

示例场景：
- 任务："翻译网页 http://example.com 的内容"
  步骤1: {"command": "curl -s http://example.com", "explanation": "获取网页内容"}
  步骤2: {"needs_llm_processing": true, "direct_response": "翻译后的内容...", "is_complete": true}

- 任务："总结README.md文件"
  步骤1: {"command": "cat README.md", "explanation": "读取文件内容"}
  步骤2: {"needs_llm_processing": true, "direct_response": "总结内容...", "is_complete": true}

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

    SYSTEM_PROMPT_DIRECT_MODE = """你是一个强大的 AI 助手，可以帮助用户完成各种任务，比如翻译、总结、分析等。

用户会给你描述一个任务，你需要直接提供答案，而不是生成 shell 命令。

你的回复必须是一个 JSON 对象，格式如下：
{
    "thinking": "你对任务的分析和思考过程",
    "direct_response": "对任务的直接响应内容",
    "explanation": "对响应的简要说明（可选）",
    "is_complete": true,
    "is_direct_mode": true
}

重要规则：
1. 直接回答用户的问题，不要生成 shell 命令
2. is_direct_mode 必须设置为 true
3. is_complete 必须设置为 true（因为这类任务一次就能完成）
4. command 字段不需要填写
5. 提供清晰、准确、有用的回答"""

    def __init__(self):
        self.messages: List[Message] = []
        self.direct_mode: bool = False  # 是否为直接LLM模式
    
    def reset(self):
        """重置对话历史"""
        self.messages = []
    
    def set_direct_mode(self, direct_mode: bool):
        """设置直接LLM模式"""
        self.direct_mode = direct_mode
    
    @property
    def system_prompt(self) -> str:
        """根据模式返回对应的系统提示"""
        return self.SYSTEM_PROMPT_DIRECT_MODE if self.direct_mode else self.SYSTEM_PROMPT_COMMAND_MODE
    
    def _build_result_message(self, result: ExecutionResult, task: str = "") -> str:
        """
        构建执行结果消息
        
        Args:
            result: 命令执行结果
            task: 原始任务描述（用于判断是否需要更多内容）
        """
        status = "成功" if result.success else "失败"
        
        # 检测任务是否可能需要LLM处理内容
        task_lower = task.lower()
        needs_more_content = any(keyword in task_lower for keyword in [
            "翻译", "translate", "总结", "summarize", "summary",
            "分析", "analyze", "analysis", "解释", "explain"
        ])
        
        # 根据任务类型选择合适的输出长度
        if needs_more_content:
            output = result.get_output_for_llm()  # 更多内容 (10000字符)
        else:
            output = result.truncated_output()  # 常规截断 (2000字符)
        
        return f"""上一条命令执行{status}：
命令: {result.command}
返回码: {result.returncode}
输出:
{output}

请根据执行结果决定下一步操作。如果任务已完成，设置 is_complete 为 true。"""

    def _build_task_message(self, task: str) -> str:
        """构建任务消息"""
        return f"请帮我完成以下任务: {task}"
    
    @abstractmethod
    def generate(self, user_input: str, last_result: Optional[ExecutionResult] = None, stream_callback: Optional[Callable[[str], None]] = None) -> LLMResponse:
        """
        生成下一步命令
        
        Args:
            user_input: 用户输入的任务描述
            last_result: 上一次命令执行的结果
            stream_callback: 流式输出回调函数
            
        Returns:
            LLMResponse: LLM 响应
        """
        pass
