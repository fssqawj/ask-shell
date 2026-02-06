"""Skill Generator from Markdown Description - Creates skill classes from markdown text"""

import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from loguru import logger
from .base_skill import BaseSkill, SkillExecutionResponse
from ..llm.openai_client import OpenAIClient
from ..skills.utils import build_full_history_message
from .skill_persistence import SkillPersistence


class SkillGenerator:
    """Generates skill classes from markdown descriptions"""
    
    def __init__(self, enable_persistence: bool = True):
        self.llm_client = OpenAIClient()
        self.enable_persistence = enable_persistence
        if enable_persistence:
            self.persistence = SkillPersistence()
        else:
            self.persistence = None
    
    def parse_markdown_to_skill(self, markdown_text: str, skill_name: str) -> type:
        """
        Parse markdown text and generate a skill class
        
        Args:
            markdown_text: Markdown description of the skill
            skill_name: Name for the generated skill class
            
        Returns:
            Generated skill class type
        """
        # Extract skill information from markdown using LLM if available
        parsed_info = self._parse_markdown_with_llm(markdown_text)
        
        # Create the skill class dynamically
        skill_instance = self._create_skill_class(
            skill_name, parsed_info
        )
        
        # Save the skill class to file if persistence is enabled
        if self.enable_persistence and self.persistence:
            self.persistence.save_skill_class(skill_instance, skill_name)
        
        return skill_instance
    
    def _parse_markdown_with_llm(self, markdown_text: str) -> Dict[str, Any]:
        """Parse markdown text to extract skill information, using LLM when available"""
        return self._extract_with_llm(markdown_text)
    
    def _extract_with_llm(self, markdown_text: str) -> Dict[str, Any]:
        """Use LLM to extract structured skill information from markdown"""
        extraction_prompt = f"""
Analyze the following markdown description of a skill and extract structured information:

{markdown_text}

Please return a JSON object with the following structure:
{{
    "name": "skill name",
    "description": "brief description of what the skill does",
    "capabilities": ["list of capabilities"],
    "system_prompt": "system prompt for the LLM to guide the skill's behavior. It should include the skill's function, usage method and examples in the skill description, as well as the output JSON format, precautions, etc. (if these contents are available)."
}}

capabilities will generate only 1-2 of the most accurate skill tags.

Focus on extracting accurate information about what the skill should do based on the description and examples."""
        
        try:
            from dataclasses import dataclass
            from typing import List
            
            @dataclass
            class ExtractionResponse:
                name: str = ""
                description: str = ""
                capabilities: List[str] = None
                system_prompt: str = ""
                
                def __post_init__(self):
                    if self.capabilities is None:
                        self.capabilities = []
            
            # Generate the extraction using the LLM
            extraction_result = self.llm_client.generate(
                system_prompt="You are a helpful assistant that extracts structured information from skill descriptions.",
                user_input=extraction_prompt,
                stream_callback=None,
                response_class=ExtractionResponse
            )
            print(extraction_result)
            return {
                'name': extraction_result.name,
                'description': extraction_result.description,
                'capabilities': extraction_result.capabilities,
                'system_prompt': extraction_result.system_prompt
            }
        except Exception as e:
            # If LLM extraction fails, fall back to regex
            logger.opt(exception=e).error("LLM extraction failed!")

    def _create_skill_class(self, skill_name: str, parsed_info: Dict[str, Any]) -> type:
        """Dynamically create a skill class based on parsed information"""
        
        class DynamicSkill(BaseSkill):
            """Dynamically generated skill class"""
            
            def __init__(self):
                super().__init__()
                self.system_prompt = parsed_info['system_prompt']
                try:
                    self.llm = OpenAIClient()
                except Exception as e:
                    # If OpenAI client fails to initialize, create a placeholder
                    # The skill will rely on simpler command generation
                    self.llm = None
            
            def get_capabilities(self) -> List[str]:
                """Return capabilities based on parsed markdown"""
                return parsed_info['capabilities']
            
            def execute(
                self,
                task: str,
                context: Optional[Dict[str, Any]] = None,
                **kwargs
            ) -> SkillExecutionResponse:
                """Execute the dynamic skill"""
                if context is None:
                    context = {}
                
                # Get execution context
                last_result = context.get('last_result')
                history = context.get('history', [])
                
                # Build user prompt with history
                user_prompt = build_full_history_message(history, task)
                
                # Call LLM to generate response if available, otherwise use simpler logic
                try:
                    from ..models.types import CommandSkillResponse
                    # Use CommandSkillResponse as default response class for dynamic skills
                    llm_response = self.llm.generate(
                        self.system_prompt, 
                        user_prompt, 
                        kwargs.get('stream_callback'), 
                        response_class=CommandSkillResponse
                    )
                    
                    return SkillExecutionResponse(
                        thinking=llm_response.thinking,
                        command=llm_response.command,
                        explanation=llm_response.explanation,
                        next_step=llm_response.next_step,
                        is_dangerous=llm_response.is_dangerous,
                        danger_reason=llm_response.danger_reason,
                        error_analysis=llm_response.error_analysis,
                        direct_response=llm_response.direct_response
                    )
                except Exception as e:
                    return SkillExecutionResponse(
                        thinking=f"LLM call failed: {str(e)}",
                        direct_response=f"Error: Failed to execute {self.name}: {str(e)}"
                    )
            
            def get_description(self) -> str:
                """Get skill description"""
                return parsed_info['description']
            
        # Set the class name dynamically
        DynamicSkill.__name__ = skill_name
        DynamicSkill.__qualname__ = skill_name
        
        return DynamicSkill()
