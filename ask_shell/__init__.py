"""Ask-Shell - 用自然语言操控你的终端"""

from .agent import AskShell
from .models.types import TaskContext, TaskStatus, ExecutionResult, LLMResponse

__version__ = "0.3.0"
__all__ = ["AskShell", "TaskContext", "TaskStatus", "ExecutionResult", "LLMResponse"]
