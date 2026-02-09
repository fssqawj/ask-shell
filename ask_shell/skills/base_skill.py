"""Base skill interface for Ask-Shell capabilities"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

from ask_shell.models.types import SkillExecutionResponse
# Import auto hint system in __init__ to avoid circular import
from ask_shell.auto_hint import get_auto_hint_system


class BaseSkill(ABC):
    """
    Base class for all Ask-Shell skills
    
    Each skill represents a capability the agent can use to accomplish tasks.
    Skills can generate commands, process content, create files, call APIs, etc.
    """
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.capabilities = self.get_capabilities()
        # Initialize auto hint system (delayed import to avoid circular import)
        self.auto_hint_system = None
        # Initialize auto hint system
        self.auto_hint_system = get_auto_hint_system()
    
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
    
    def _build_hints_info(self) -> str:
        """
        Build hints information for this skill
        
        This method can be overridden by subclasses to provide
        skill-specific hints. By default, it loads auto-generated hints.
        
        Returns:
            Formatted hints string
        """
        return self._load_auto_hints()
    
    def _load_auto_hints(self) -> str:
        """
        Load auto-generated hints from the hint system
        
        Returns:
            Formatted hints string
        """
        try:
            # Lazy initialize auto hint system
            if self.auto_hint_system is None:
                from ask_shell.auto_hint import get_auto_hint_system
                self.auto_hint_system = get_auto_hint_system()
            
            # Get skill name for hint lookup
            skill_name = self.__class__.__name__
            
            # Load hints for this skill
            skill_hints = self.auto_hint_system.get_hints_for_skill(skill_name, max_hints=2)
            
            # Load general hints (cross-skill patterns)
            general_hints = self.auto_hint_system.get_hints_for_skill("general", max_hints=1)
            
            # Combine both types of hints
            hints = skill_hints + general_hints
            
            if not hints:
                return ""
            
            hint_lines = ["基于历史执行经验的建议："]
            for i, hint in enumerate(hints, 1):
                metadata = hint.get("metadata", {})
                content = hint.get("content", "")
                
                hint_lines.append(f"\n{i}. {metadata.get('title', '提示')}:")
                hint_lines.append(f"   {content}")
                
                # Record hint usage
                if "id" in metadata:
                    self.auto_hint_system.record_hint_usage(metadata["id"])
            
            return "\n".join(hint_lines)
            
        except Exception as e:
            from loguru import logger
            logger.warning(f"Failed to load auto hints for {self.__class__.__name__}: {e}")
            return ""
