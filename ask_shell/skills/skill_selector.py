"""Intelligent Skill Selector using LLM"""

import json
from typing import List, Optional, Dict, Any
from .base_skill import BaseSkill


class SkillSelector:
    """
    Uses LLM to intelligently select the most appropriate skill for a task
    
    Instead of keyword matching, this selector:
    1. Provides LLM with all available skills and their descriptions
    2. LLM analyzes the task and chooses the best skill
    3. Can switch skills dynamically during task execution
    """
    
    SKILL_SELECTION_PROMPT = """你是一个智能技能选择器。根据用户任务和可用技能，选择最合适的技能来完成任务。

可用技能列表：
{skills_description}

你的回复必须是一个 JSON 对象，格式如下：
{{
    "selected_skill": "技能名称",
    "confidence": 0.95,
    "reasoning": "选择该技能的理由",
    "alternative_skills": ["备选技能1", "备选技能2"]
}}

选择规则：
1. 仔细分析任务的本质需求
2. 优先选择最专业的技能（例如：创建PPT就选PPTSkill，生成图片就选ImageSkill）
3. 只有当任务需要执行shell命令或内容处理时，才选择LLMSkill
4. confidence 应该反映你对选择的确信程度（0.0-1.0）
5. 如果任务可能需要多个技能配合，在alternative_skills中列出

用户任务：{task}

当前执行上下文：
{context}
"""
    
    def __init__(self, llm_client):
        """
        Initialize skill selector
        
        Args:
            llm_client: LLM client for intelligent selection
        """
        self.llm = llm_client
    
    def select_skill(
        self,
        task: str,
        available_skills: List[BaseSkill],
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[BaseSkill, float, str]:
        """
        Use LLM to select the best skill for the task
        
        Args:
            task: Task description
            available_skills: List of available skills
            context: Execution context (history, iteration, etc.)
            
        Returns:
            Tuple of (selected_skill, confidence, reasoning)
        """
        # Build skills description for LLM
        skills_description = self._build_skills_description(available_skills)
        
        # Build context description
        context_description = self._build_context_description(context)
        
        # Create prompt
        prompt = self.SKILL_SELECTION_PROMPT.format(
            skills_description=skills_description,
            task=task,
            context=context_description
        )
        
        # Call LLM for skill selection
        try:
            response = self._call_llm_for_selection(prompt)
            
            # Parse LLM response
            selected_skill_name = response.get("selected_skill", "LLMSkill")
            confidence = float(response.get("confidence", 0.8))
            reasoning = response.get("reasoning", "LLM选择的技能")
            
            # Find the skill object
            selected_skill = self._find_skill_by_name(available_skills, selected_skill_name)
            
            if selected_skill is None:
                # Fallback to first skill (should be default LLMSkill)
                selected_skill = available_skills[0]
                confidence = 0.7
                reasoning = f"未找到'{selected_skill_name}'，使用默认技能"
            
            return selected_skill, confidence, reasoning
            
        except Exception as e:
            # Fallback to first skill
            return available_skills[0], 0.5, f"选择失败，使用默认技能: {str(e)}"
    
    def _build_skills_description(self, skills: List[BaseSkill]) -> str:
        """Build formatted description of all available skills"""
        descriptions = []
        for i, skill in enumerate(skills, 1):
            capabilities = [c.value for c in skill.capabilities]
            descriptions.append(
                f"{i}. **{skill.name}**\n"
                f"   - 能力: {', '.join(capabilities)}\n"
                f"   - 描述: {skill.get_description()}\n"
            )
        return "\n".join(descriptions)
    
    def _build_context_description(self, context: Optional[Dict[str, Any]]) -> str:
        """Build formatted context description"""
        if not context:
            return "无执行历史"
        
        iteration = context.get('iteration', 0)
        has_history = len(context.get('history', [])) > 0
        last_result = context.get('last_result')
        
        desc = f"- 当前步骤: 第{iteration}步\n"
        
        if last_result:
            status = "成功" if last_result.success else "失败"
            desc += f"- 上一步结果: {status}\n"
            desc += f"- 上一条命令: {last_result.command}\n"
        else:
            desc += "- 上一步结果: 无（这是第一步）\n"
        
        return desc
    
    def _call_llm_for_selection(self, prompt: str) -> Dict[str, Any]:
        """
        Call LLM to get skill selection
        
        Args:
            prompt: Selection prompt
            
        Returns:
            Parsed JSON response
        """
        from ..models.types import Message
        
        # Real LLM call for skill selection
        try:
            # Use a simple API call to get JSON response
            messages = [
                Message(role="system", content="You are a skill selector. Always respond with valid JSON."),
                Message(role="user", content=prompt)
            ]
            
            # Call the LLM
            if hasattr(self.llm, 'client') and self.llm.client:
                # OpenAI client
                completion = self.llm.client.chat.completions.create(
                    model=self.llm.model,
                    messages=[{"role": m.role, "content": m.content} for m in messages],
                    temperature=0.3,  # Lower temperature for more deterministic selection
                    max_tokens=500
                )
                response_text = completion.choices[0].message.content.strip()
                
                # Try to parse JSON from response
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    # Try to extract JSON if wrapped in other text
                    import re
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    else:
                        raise ValueError(f"Cannot parse JSON from response: {response_text}")
            else:
                # Fallback
                return {
                    "selected_skill": "LLMSkill",
                    "confidence": 0.8,
                    "reasoning": "LLM客户端不可用，使用默认技能"
                }
                
        except Exception as e:
            return {
                "selected_skill": "LLMSkill",
                "confidence": 0.5,
                "reasoning": f"LLM调用失败: {str(e)}，使用默认技能"
            }
    
    def _find_skill_by_name(self, skills: List[BaseSkill], name: str) -> Optional[BaseSkill]:
        """Find skill by name (case-insensitive)"""
        name_lower = name.lower()
        for skill in skills:
            if skill.name.lower() == name_lower:
                return skill
        return None
