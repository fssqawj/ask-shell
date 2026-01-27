"""数据模型定义"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """命令执行结果"""
    command: str
    returncode: int
    stdout: str
    stderr: str
    
    @property
    def success(self) -> bool:
        return self.returncode == 0
    
    @property
    def output(self) -> str:
        """获取合并的输出"""
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(f"[stderr] {self.stderr}")
        return "\n".join(parts) if parts else "(无输出)"
    
    def truncated_output(self, max_length: int = 2000) -> str:
        """获取截断的输出"""
        output = self.output
        if len(output) > max_length:
            return output[:max_length] + "\n...(输出已截断)"
        return output


@dataclass
class LLMResponse:
    """LLM 响应结构"""
    thinking: str = ""
    command: str = ""
    explanation: str = ""
    is_complete: bool = False
    next_step: str = ""
    error_analysis: str = ""
    is_dangerous: bool = False  # 是否为危险操作
    danger_reason: str = ""     # 危险原因说明
    
    @classmethod
    def from_dict(cls, data: dict) -> "LLMResponse":
        return cls(
            thinking=data.get("thinking", ""),
            command=data.get("command", ""),
            explanation=data.get("explanation", ""),
            is_complete=data.get("is_complete", False),
            next_step=data.get("next_step", ""),
            error_analysis=data.get("error_analysis", ""),
            is_dangerous=data.get("is_dangerous", False),
            danger_reason=data.get("danger_reason", "")
        )


@dataclass
class Message:
    """对话消息"""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class TaskContext:
    """任务上下文"""
    task_description: str
    status: TaskStatus = TaskStatus.PENDING
    iteration: int = 0
    history: List[ExecutionResult] = field(default_factory=list)
    
    def add_result(self, result: ExecutionResult):
        """添加执行结果到历史"""
        self.history.append(result)
    
    @property
    def last_result(self) -> Optional[ExecutionResult]:
        """获取最后一次执行结果"""
        return self.history[-1] if self.history else None
