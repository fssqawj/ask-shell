"""Base skill interface for Ask-Shell capabilities"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

from ask_shell.models.types import SkillExecutionResponse


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
    def get_capabilities(self) -> List[str]:
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
    ) -> SkillExecutionResponse:
        """
        Execute the skill to accomplish the task
        
        Args:
            task: The task description
            context: Execution context (history, last result, etc.)
            **kwargs: Additional skill-specific parameters
            
        Returns:
            SkillExecutionResponse with the result
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
