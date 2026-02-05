"""Skill Persistence - Save and load generated skills as Python files"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import Optional, Type
from loguru import logger

from .base_skill import BaseSkill


class SkillPersistence:
    """Handles saving and loading skill classes as Python files"""
    
    def __init__(self, skills_dir: Optional[str] = None):
        """
        Initialize skill persistence
        
        Args:
            skills_dir: Directory to store generated skill files. 
                       Defaults to skills/generated_skills/
        """
        if skills_dir is None:
            # Default to ask_shell/skills/generated_skills/
            current_dir = Path(__file__).parent
            self.skills_dir = current_dir / "generated_skills"
        else:
            self.skills_dir = Path(skills_dir)
        
        # Create directory if it doesn't exist
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Skill persistence directory: {self.skills_dir}")
    
    def save_skill_class(self, skill_class: Type[BaseSkill], skill_name: str) -> bool:
        """
        Save a skill class as a Python file
        
        Args:
            skill_class: The skill class to save
            skill_name: Name of the skill (will be used as filename)
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create filename (snake_case from skill name)
            filename = self._skill_name_to_filename(skill_name)
            file_path = self.skills_dir / f"{filename}.py"
            
            # Generate Python code for the class
            python_code = self._generate_skill_code(skill_class, skill_name)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(python_code)
            
            logger.info(f"Saved skill '{skill_name}' to {file_path}")
            return True
            
        except Exception as e:
            logger.opt(exception=e).error(f"Failed to save skill '{skill_name}': {e}")
            return False
    
    def load_skill_class(self, skill_name: str) -> Optional[Type[BaseSkill]]:
        """
        Load a skill class from a Python file
        
        Args:
            skill_name: Name of the skill to load
            
        Returns:
            Skill class if loaded successfully, None otherwise
        """
        try:
            # Create filename
            filename = self._skill_name_to_filename(skill_name)
            file_path = self.skills_dir / f"{filename}.py"
            
            # Check if file exists
            if not file_path.exists():
                logger.debug(f"Skill file not found: {file_path}")
                return None
            
            # Import the module
            module_name = f"generated_skill_{filename}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.error(f"Failed to create module spec for {file_path}")
                return None
                        
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            # Add the current directory to the module's globals to help with relative imports
            module.__package__ = 'ask_shell.skills.generated_skills'
            spec.loader.exec_module(module)
            
            # Get the skill class (should match the filename)
            class_name = self._filename_to_class_name(filename)
            if hasattr(module, class_name):
                skill_class = getattr(module, class_name)
                logger.info(f"Loaded skill '{skill_name}' from {file_path}")
                return skill_class
            else:
                logger.error(f"Class '{class_name}' not found in module {module_name}")
                return None
                
        except Exception as e:
            logger.opt(exception=e).error(f"Failed to load skill '{skill_name}': {e}")
            return None
    
    def skill_exists(self, skill_name: str) -> bool:
        """
        Check if a skill file exists for the given skill name
        
        Args:
            skill_name: Name of the skill to check
            
        Returns:
            True if skill file exists, False otherwise
        """
        filename = self._skill_name_to_filename(skill_name)
        file_path = self.skills_dir / f"{filename}.py"
        return file_path.exists()
    
    def _skill_name_to_filename(self, skill_name: str) -> str:
        """
        Convert skill name to filename (snake_case)
        
        Examples:
            "MacSay" -> "mac_say"
            "Browser Automation" -> "browser_automation"
        """
        # Handle Chinese characters and spaces
        name = skill_name.replace(' ', '_')
        # Convert to snake_case
        import re
        # Insert underscore before capital letters (except first)
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name)
        return name.lower()
    
    def _filename_to_class_name(self, filename: str) -> str:
        """
        Convert filename to class name (PascalCase)
        
        Examples:
            "mac_say" -> "MacSay"
            "browser_automation" -> "BrowserAutomation"
        """
        # Split by underscore and capitalize each part
        parts = filename.split('_')
        class_name = ''.join(part.capitalize() for part in parts)
        return class_name
    
    def _generate_skill_code(self, skill_class: Type[BaseSkill], skill_name: str) -> str:
        """
        Generate Python code for a skill class
        
        Args:
            skill_class: The skill class instance
            skill_name: Name of the skill
            
        Returns:
            Generated Python code as string
        """
        # Get class name
        class_name = self._filename_to_class_name(self._skill_name_to_filename(skill_name))
        
        # Get the system prompt and other attributes
        system_prompt = getattr(skill_class, 'system_prompt', '')
        capabilities = skill_class.get_capabilities()
        
        # Escape quotes in system prompt
        escaped_prompt = repr(system_prompt)[1:-1]  # Remove outer quotes from repr
        
        # Generate the Python code
        code = f'''"""Generated skill: {skill_name}"""

from typing import List, Dict, Any, Optional
from ask_shell.skills.base_skill import BaseSkill
from ask_shell.models.types import SkillExecutionResponse
from ask_shell.llm.openai_client import OpenAIClient
from ask_shell.skills.utils import build_full_history_message


class {class_name}(BaseSkill):
    """{skill_class.get_description()}"""
    
    def __init__(self):
        super().__init__()
        self.system_prompt = """{escaped_prompt}"""
        try:
            self.llm = OpenAIClient()
        except Exception:
            self.llm = None
    
    def get_capabilities(self) -> List[str]:
        """Return the capabilities of this skill"""
        return {capabilities!r}
    
    def get_description(self) -> str:
        """Get skill description"""
        return "{skill_class.get_description()}"
    
    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SkillExecutionResponse:
        """Execute the skill"""
        if context is None:
            context = {{}}
        
        # Get execution context
        last_result = context.get('last_result')
        history = context.get('history', [])
        
        # Build user prompt with history
        user_prompt = build_full_history_message(history, task)
        
        # Call LLM to generate response
        try:
            from ask_shell.models.types import CommandSkillResponse
            llm_response = self.llm.generate(
                self.system_prompt,
                user_prompt,
                kwargs.get('stream_callback'),
                response_class=CommandSkillResponse
            )
            
            return SkillExecutionResponse(
                thinking=llm_response.thinking,
                command=llm_response.command + " & echo 命令执行成功",
                explanation=llm_response.explanation,
                next_step=llm_response.next_step,
                is_dangerous=llm_response.is_dangerous,
                danger_reason=llm_response.danger_reason,
                error_analysis=llm_response.error_analysis,
                direct_response=llm_response.direct_response
            )
        except Exception as e:
            return SkillExecutionResponse(
                thinking=f"LLM call failed: {{str(e)}}",
                direct_response=f"Error: Failed to execute {{self.name}}: {{str(e)}}"
            )
'''
        return code