"""Base skill interface for Ask-Shell capabilities"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class SkillCapability(Enum):
    """Types of capabilities a skill can provide"""
    COMMAND_GENERATION = "command_generation"  # Generate and execute shell commands
    LLM_PROCESSING = "llm_processing"  # Process content with LLM (translate, summarize, etc.)
    FILE_GENERATION = "file_generation"  # Generate files (PPT, images, videos, etc.)
    WEB_INTERACTION = "web_interaction"  # Interact with web services/APIs
    DATA_ANALYSIS = "data_analysis"  # Analyze and visualize data


@dataclass
class SkillResponse:
    """
    Unified response format for all skills
    
    This replaces the old LLMResponse and provides a common interface
    for all skill types.
    """
    # Core fields
    skill_name: str  # Which skill generated this response
    thinking: str = ""  # Reasoning process
    is_complete: bool = False  # Whether the task is finished
    
    # Command execution fields (for command generation skills)
    command: str = ""  # Shell command to execute
    explanation: str = ""  # Command explanation
    next_step: str = ""  # Next planned step
    is_dangerous: bool = False  # Safety flag
    danger_reason: str = ""  # Danger explanation
    error_analysis: str = ""  # Error analysis if previous command failed
    
    # Direct response fields (for LLM/content processing skills)
    direct_response: str = ""  # Direct content output
    needs_llm_processing: bool = False  # Whether next step needs LLM
    
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
    
    @classmethod
    def from_dict(cls, data: dict) -> "SkillResponse":
        """Create SkillResponse from dictionary"""
        return cls(
            skill_name=data.get("skill_name", "unknown"),
            thinking=data.get("thinking", ""),
            is_complete=data.get("is_complete", False),
            command=data.get("command", ""),
            explanation=data.get("explanation", ""),
            next_step=data.get("next_step", ""),
            is_dangerous=data.get("is_dangerous", False),
            danger_reason=data.get("danger_reason", ""),
            error_analysis=data.get("error_analysis", ""),
            direct_response=data.get("direct_response", ""),
            needs_llm_processing=data.get("needs_llm_processing", False),
            generated_files=data.get("generated_files", []),
            file_metadata=data.get("file_metadata", {}),
            api_response=data.get("api_response", {}),
            service_status=data.get("service_status", "")
        )


class BaseSkill(ABC):
    """
    Base class for all Ask-Shell skills
    
    Each skill represents a capability the agent can use to accomplish tasks.
    Skills can generate commands, process content, create files, call APIs, etc.
    """
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.capabilities = self.get_capabilities()
    
    @abstractmethod
    def get_capabilities(self) -> List[SkillCapability]:
        """
        Return list of capabilities this skill provides
        
        Returns:
            List of SkillCapability enums
        """
        pass
    
    @abstractmethod
    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SkillResponse:
        """
        Execute the skill to accomplish the task
        
        Args:
            task: The task description
            context: Execution context (history, last result, etc.)
            **kwargs: Additional skill-specific parameters
            
        Returns:
            SkillResponse with the result
        """
        pass
    
    def get_description(self) -> str:
        """
        Get human-readable description of what this skill does
        
        Returns:
            Description string
        """
        return f"{self.name}: A skill with capabilities {[c.value for c in self.capabilities]}"
    
    def reset(self):
        """
        Reset skill state (optional, override if needed)
        
        Called when starting a new task or conversation.
        """
        pass
