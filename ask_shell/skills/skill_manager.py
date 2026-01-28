"""Skill Manager for routing tasks to appropriate skills"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
from .base_skill import BaseSkill, SkillResponse
from .skill_selector import SkillSelector

if TYPE_CHECKING:
    from ..ui.console import ConsoleUI


class SkillManager:
    """
    Manages all available skills and routes tasks to the appropriate skill
    
    The SkillManager:
    1. Registers available skills
    2. Uses LLM to intelligently select which skill should handle a task
    3. Executes the selected skill
    4. Manages skill lifecycle (reset, etc.)
    """
    
    def __init__(self, llm_client=None, ui=None):
        """
        Initialize SkillManager
        
        Args:
            llm_client: LLM client for intelligent skill selection
            ui: ConsoleUI instance for displaying selection process
        """
        self.skills: List[BaseSkill] = []
        self.default_skill: Optional[BaseSkill] = None
        self.skill_selector = SkillSelector(llm_client) if llm_client else None
        self.ui = ui
    
    def register_skill(self, skill: BaseSkill, is_default: bool = False):
        """
        Register a new skill
        
        Args:
            skill: The skill instance to register
            is_default: If True, this skill will be used as fallback
        """
        self.skills.append(skill)
        if is_default:
            self.default_skill = skill
    
    def select_skill(self, task: str, context: Optional[Dict[str, Any]] = None) -> Optional[BaseSkill]:
        """
        Select the best skill to handle the given task using LLM-based intelligent selection
        
        Args:
            task: The task description
            context: Optional context for decision making
            
        Returns:
            The selected skill, or default skill if no match found
        """
        # Use intelligent LLM-based selection
        if self.skill_selector:
            try:
                # Show animation if UI is available
                if self.ui:
                    with self.ui.skill_selection_animation():
                        selected_skill, confidence, reasoning = self.skill_selector.select_skill(
                            task, self.skills, context
                        )
                    
                    # Display beautiful selection result
                    self.ui.print_skill_selected(
                        skill_name=selected_skill.name,
                        confidence=confidence,
                        reasoning=reasoning,
                        capabilities=[c.value for c in selected_skill.capabilities]
                    )
                else:
                    # No UI, just select
                    selected_skill, confidence, reasoning = self.skill_selector.select_skill(
                        task, self.skills, context
                    )
                    print(f"[SkillManager] 🎯 Selected: {selected_skill.name} (confidence: {confidence:.2f})")
                    print(f"[SkillManager] 💭 Reasoning: {reasoning}")
                
                return selected_skill
            except Exception as e:
                if self.ui:
                    self.ui.print_error(f"Intelligent selection failed: {e}, using default skill")
                else:
                    print(f"[SkillManager] ⚠️  Intelligent selection failed: {e}, using default skill")
                return self.default_skill
        
        # No skill selector configured, use default skill
        if self.default_skill:
            if self.ui:
                self.ui.print_warning(f"Using default skill: {self.default_skill.name}")
            else:
                print(f"[SkillManager] Using default skill: {self.default_skill.name}")
            return self.default_skill
        
        return None
    
    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        force_skill: Optional[str] = None,
        **kwargs
    ) -> SkillResponse:
        """
        Execute a task using the appropriate skill
        
        Args:
            task: The task to execute
            context: Execution context
            force_skill: Force use of specific skill by name
            **kwargs: Additional parameters passed to skill
            
        Returns:
            SkillResponse from the executed skill
        """
        # Select skill
        if force_skill:
            skill = self.get_skill_by_name(force_skill)
            if not skill:
                return SkillResponse(
                    skill_name="error",
                    thinking=f"Skill '{force_skill}' not found",
                    is_complete=True,
                    direct_response=f"Error: No skill named '{force_skill}' is registered."
                )
        else:
            skill = self.select_skill(task, context)
        
        if not skill:
            return SkillResponse(
                skill_name="error",
                thinking="No suitable skill found and no default skill configured",
                is_complete=True,
                direct_response="Error: Unable to find a skill to handle this task."
            )
        
        # Execute the selected skill
        try:
            return skill.execute(task, context, **kwargs)
        except Exception as e:
            return SkillResponse(
                skill_name=skill.name,
                thinking=f"Skill execution failed: {str(e)}",
                is_complete=True,
                direct_response=f"Error executing {skill.name}: {str(e)}"
            )
    
    def get_skill_by_name(self, name: str) -> Optional[BaseSkill]:
        """Get a skill by its name"""
        for skill in self.skills:
            if skill.name.lower() == name.lower():
                return skill
        return None
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """
        List all registered skills with their information
        
        Returns:
            List of skill information dictionaries
        """
        return [
            {
                "name": skill.name,
                "capabilities": [c.value for c in skill.capabilities],
                "description": skill.get_description()
            }
            for skill in self.skills
        ]
    
    def reset_all(self):
        """Reset state for all skills"""
        for skill in self.skills:
            skill.reset()
