"""Skills module for Ask-Shell

This module provides a flexible skill system that allows the agent to have
various capabilities beyond just shell command generation.
"""

from .base_skill import BaseSkill, SkillResponse, SkillCapability
from .skill_manager import SkillManager
from .skill_selector import SkillSelector
from .llm_skill import LLMSkill
from .ppt_skill import PPTSkill
from .image_skill import ImageSkill
from .browser_skill import BrowserSkill

__all__ = [
    'BaseSkill', 
    'SkillResponse', 
    'SkillCapability', 
    'SkillManager',
    'SkillSelector',
    'LLMSkill',
    'PPTSkill',
    'ImageSkill',
    'BrowserSkill'
]
