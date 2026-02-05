"""数据模型定义"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..skills.base_skill import BaseSkill


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SkillSelectResponse:
    skill_name: str = ""
    skill: Optional["BaseSkill"] = None
    select_reason: str = ""
    task_complete: Optional[bool] = None  # Whether the overall task is complete (determined by skill selector)


# Define dataclasses for LLM responses based on prompt schemas
@dataclass
class CommandSkillResponse:
    """Dataclass for CommandSkill LLM response - matches the JSON schema expected by the prompt"""
    thinking: str = ""
    command: str = ""
    explanation: str = ""
    next_step: str = ""
    error_analysis: str = ""
    is_dangerous: bool = False
    danger_reason: str = ""
    direct_response: str = ""  # For AI processing mode

@dataclass
class DirectLLMSkillResponse:
    """Dataclass for DirectLLMSkill LLM response - matches the JSON schema expected by the prompt"""
    thinking: str = ""
    direct_response: str = ""

@dataclass
class PPTSkillResponse:
    """Dataclass for PPTSkill LLM response - matches the JSON schema expected by the prompt"""
    title: str = ""
    outline: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.outline is None:
            self.outline = []

@dataclass
class BrowserSkillResponse:
    """Dataclass for BrowserSkill LLM response - matches the JSON schema expected by the prompt"""
    thinking: str = ""
    code: str = ""
    explanation: str = ""


@dataclass
class SkillExecutionResponse:
    thinking: str = ""  # Reasoning process
    # Command execution fields (for command generation skills)
    command: str = ""  # Shell command to execute
    explanation: str = ""  # Command explanation
    next_step: str = ""  # Next planned step
    is_dangerous: bool = False  # Safety flag
    danger_reason: str = ""  # Danger explanation
    error_analysis: str = ""  # Error analysis if previous command failed
    
    # Direct response fields (for LLM/content processing skills)
    direct_response: str = ""  # Direct content output
    
    # File generation fields (for file creation skills)
    generated_files: List[str] = None  # Paths to generated files
    file_metadata: Dict[str, Any] = None  # Additional file information
    
    # API/Service fields (for external service skills)
    api_response: Dict[str, Any] = None  # Response from external APIs
    service_status: str = ""  # Status of service interaction

    def __post_init__(self):
        if self.generated_files is None:
            self.generated_files = []
        if self.file_metadata is None:
            self.file_metadata = {}
        if self.api_response is None:
            self.api_response = {}


@dataclass
class SkillResponse(SkillSelectResponse, SkillExecutionResponse):
    """
    Unified response format for all skills
    
    This replaces the old LLMResponse and provides a common interface
    for all skill types.
    """
    pass


@dataclass
class ExecutionResult:
    """命令执行结果"""
    command: str
    returncode: int
    stdout: str
    stderr: str
    skill_response: Optional[SkillResponse] = None
    
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
    
    def get_output_for_llm(self, max_length: int = 10000) -> str:
        """获取用于LLM处理的输出（更大的限制）"""
        output = self.output
        if len(output) > max_length:
            return output[:max_length] + f"\n...(输出已截断，仅显示前{max_length}字符)"
        return output


@dataclass
class LLMResponse:
    """LLM 响应结构 - 保留用于向后兼容，但主要使用 raw_json 字段"""
    raw_json: str = ""  # Raw JSON response from LLM
    
    @classmethod
    def from_json(cls, json_str: str) -> "LLMResponse":
        return cls(raw_json=json_str)


@dataclass
class Message:
    """对话消息"""
    role: str  # "system", "user", "assistant"
    content: str



