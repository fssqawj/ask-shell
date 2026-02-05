"""Skills module for Ask-Shell

This module provides a flexible skill system that allows the agent to have
various capabilities beyond just shell command generation.
"""

from .base_skill import BaseSkill
from .skill_manager import SkillManager
from .skill_selector import SkillSelector
from .command_skill import CommandSkill
from .direct_llm_skill import DirectLLMSkill
from .ppt_skill import PPTSkill
from .image_skill import ImageSkill
from .browser_skill import BrowserSkill
from .wechat_skill import WeChatSkill
from .feishu_skill import FeishuSkill

__all__ = [
    'BaseSkill', 
    'SkillManager',
    'SkillSelector',
    'CommandSkill',
    'DirectLLMSkill',
    'PPTSkill',
    'ImageSkill',
    'BrowserSkill',
    'WeChatSkill',
    'FeishuSkill'
]
