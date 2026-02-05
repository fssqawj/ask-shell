"""Skill Manager for routing tasks to appropriate skills"""
import os
from loguru import logger
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from .skill_selector import SkillSelector
from .base_skill import BaseSkill
from ..models.types import SkillSelectResponse, SkillResponse
from .command_skill import CommandSkill
from .direct_llm_skill import DirectLLMSkill
from .image_skill import ImageSkill
from .ppt_skill import PPTSkill
from .browser_skill import BrowserSkill
from .wechat_skill import WeChatSkill
from .feishu_skill import FeishuSkill
from .skill_generator import SkillGenerator
from .skill_persistence import SkillPersistence

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
    
    def __init__(self, ui=None, enable_persistence: bool = True):
        """
        Initialize SkillManager
        
        Args:
            llm_client: LLM client for intelligent skill selection
            ui: ConsoleUI instance for displaying selection process
            enable_persistence: Whether to enable skill persistence
        """
        self.skills: List[BaseSkill] = []
        self.default_skill: Optional[BaseSkill] = None
        self.skill_selector = SkillSelector()
        self.ui = ui
        self.enable_persistence = enable_persistence
        if enable_persistence:
            self.persistence = SkillPersistence()
        else:
            self.persistence = None
        self.register_skill()
        self.register_dynamic_skill()
    
    def register_skill(self):
        """注册所有可用技能"""
        # 注册命令生成技能（默认技能）
        command_skill = CommandSkill()
        self.skills.append(command_skill)
        self.default_skill = command_skill

        # 注册直接LLM处理技能
        direct_llm_skill = DirectLLMSkill()
        self.skills.append(direct_llm_skill)
        
        # 注册PPT生成技能
        ppt_skill = PPTSkill()
        self.skills.append(ppt_skill)
        
        # 注册图片生成技能
        image_skill = ImageSkill()
        self.skills.append(image_skill)
        
        # 注册浏览器自动化技能
        browser_skill = BrowserSkill()
        self.skills.append(browser_skill)
        
        # 注册WeChat自动化技能
        wechat_skill = WeChatSkill()
        self.skills.append(wechat_skill)
        
        # 注册Feishu自动化技能
        feishu_skill = FeishuSkill()
        self.skills.append(feishu_skill)
    
    def register_dynamic_skill(self):
        """Register dynamic skills"""
        skill_generator = SkillGenerator(enable_persistence=self.enable_persistence)
        custom_skills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_skills")
        logger.info(f"Load custom skills from directory: {custom_skills_dir}")
        
        for file_name in os.listdir(custom_skills_dir):
            if file_name.endswith(".md"):
                skill_name = file_name[:-3]
                
                # Try to load from persisted Python file first
                skill = None
                if self.enable_persistence and self.persistence:
                    if self.persistence.skill_exists(skill_name):
                        skill_class = self.persistence.load_skill_class(skill_name)
                        if skill_class:
                            skill = skill_class()
                            logger.info(f"Loaded skill '{skill_name}' from persisted file")
                
                # If not loaded from file, generate from markdown
                if skill is None:
                    file_content = open(os.path.join(custom_skills_dir, file_name), "r", encoding="utf-8").read()
                    skill = skill_generator.parse_markdown_to_skill(file_content, skill_name)
                    logger.info(f"Generated skill '{skill_name}' from markdown")
                
                logger.info(f"Registering dynamic skill:\n {skill.name=}\n, {skill.get_description()=}\n, {skill.get_capabilities()=}\n")
                self.skills.append(skill)
    
    def select_skill(self, task: str, context: Optional[Dict[str, Any]] = None) -> Optional[SkillSelectResponse]:
        """
        Select the best skill to handle the given task using LLM-based intelligent selection
        
        Args:
            task: The task description
            context: Optional context for decision making
            
        Returns:
            SkillSelectResponse with the selected skill and selection information, or default skill if no match found
        """
        # Use intelligent LLM-based selection
        try:
            with self.ui.skill_selection_animation():
                selected_skill, confidence, reasoning, task_complete = self.skill_selector.select_skill(
                    task, self.skills, context
                )
            if task_complete:
                return SkillSelectResponse(skill=None, skill_name="none", task_complete=True, select_reason="Task completed")
            if selected_skill:
                self.ui.print_skill_selected(
                    skill_name=selected_skill.name,
                    confidence=confidence,
                    reasoning=reasoning,
                    capabilities=selected_skill.capabilities
                )
                return SkillSelectResponse(skill=selected_skill, skill_name=selected_skill.name, task_complete=task_complete, select_reason=reasoning)
        except Exception as e:
            logger.opt(exception=e).error(f"Intelligent selection failed: {e}, using default skill")
            if self.ui:
                self.ui.print_error(f"Intelligent selection failed: {e}, using default skill")
            else:
                logger.warning(f"[SkillManager] Intelligent selection failed: {e}, using default skill")
        return SkillSelectResponse(skill=self.default_skill, skill_name=self.default_skill.name if self.default_skill else "unknown", task_complete=False, select_reason="Fallback due to selection error")
    
    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SkillResponse:
        """
        Execute a task using the appropriate skill
        
        Args:
            task: The task to execute
            context: Execution context
            **kwargs: Additional parameters passed to skill
            
        Returns:
            SkillResponse from the executed skill
        """
        # Select skill
        skill_select_response = self.select_skill(task, context) 
        if not skill_select_response:
            return SkillResponse(
                skill_name="error",
                thinking="No suitable skill found and no default skill configured",
                task_complete=True,
                direct_response="Error: Unable to find a skill to handle this task."
            )
        if skill_select_response.task_complete:
            return SkillResponse(
                skill_name="none",
                thinking="Task completed",
                task_complete=True,
                direct_response="Task completed."
            ) 
        # Execute the selected skill
        try:
            with self.ui.streaming_display() as stream_callback:
                skill_exec_response = skill_select_response.skill.execute(task, context, stream_callback=stream_callback)
                skill_response = SkillResponse(
                    skill=skill_select_response.skill,
                    skill_name=skill_select_response.skill_name, 
                    select_reason=skill_select_response.select_reason,
                    task_complete=skill_select_response.task_complete, 
                    thinking=skill_exec_response.thinking,
                    command=skill_exec_response.command,
                    explanation=skill_exec_response.explanation,
                    next_step=skill_exec_response.next_step,
                    is_dangerous=skill_exec_response.is_dangerous,
                    danger_reason=skill_exec_response.danger_reason,
                    error_analysis=skill_exec_response.error_analysis,
                    direct_response=skill_exec_response.direct_response,
                    generated_files=skill_exec_response.generated_files,
                    file_metadata=skill_exec_response.file_metadata,
                    api_response=skill_exec_response.api_response,
                    service_status=skill_exec_response.service_status
                )
                return skill_response
        except Exception as e:
            logger.opt(exception=e).error(f"Skill execution failed: {str(e)}")
            return SkillResponse(
                skill=skill_select_response.skill,
                skill_name=skill_select_response.skill_name,
                select_reason=skill_select_response.select_reason,
                thinking=f"Skill execution failed: {str(e)}",
                task_complete=True,
                direct_response=f"Error executing {skill_select_response.skill_name}: {str(e)}"
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
