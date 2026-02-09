"""Hint Generator - Generate hints content from discovered patterns"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from loguru import logger

from ..llm.openai_client import OpenAIClient
from .types import HintPattern, HintCategory, HintMetadata, ExecutionAnalysisResult


class HintGenerator:
    """
    Generates hints content from discovered patterns using LLM
    """
    
    def __init__(self, enable_llm=True):
        self.enable_llm = enable_llm
        try:
            if enable_llm:
                self.llm = OpenAIClient()
            else:
                self.llm = None
        except Exception:
            self.llm = None
            self.enable_llm = False
        self.max_hints_per_category = 5  # Limit hints per category to avoid overwhelming
        
    def generate_hints_from_analysis(self, analysis_result: ExecutionAnalysisResult, 
                                   task_description: str = "") -> List[Dict[str, Any]]:
        """
        Generate hints from analysis results
        
        Args:
            analysis_result: Analysis result from ExecutionResultAnalyzer
            task_description: Original task description for context
            
        Returns:
            List of generated hints with metadata
        """
        hints = []
        
        # Generate hints for different categories
        hints.extend(self._generate_success_hints(analysis_result.success_patterns, task_description))
        hints.extend(self._generate_failure_hints(analysis_result.failure_patterns, task_description))
        hints.extend(self._generate_best_practice_hints(analysis_result, task_description))
        hints.extend(self._generate_troubleshooting_hints(analysis_result.failure_patterns, task_description))
        
        logger.info(f"Generated {len(hints)} hints from analysis")
        return hints
    
    def _generate_success_hints(self, patterns: List[HintPattern], 
                               task_description: str) -> List[Dict[str, Any]]:
        """Generate hints from successful patterns"""
        hints = []
        
        # Group patterns by skill
        skill_patterns = {}
        for pattern in patterns:
            if pattern.skill_name not in skill_patterns:
                skill_patterns[pattern.skill_name] = []
            skill_patterns[pattern.skill_name].append(pattern)
        
        # Generate hints for each skill
        for skill_name, skill_patterns_list in skill_patterns.items():
            if len(hints) >= self.max_hints_per_category:
                break
                
            # Combine similar patterns
            combined_pattern = self._combine_patterns(skill_patterns_list)
            
            hint_content = self._generate_success_hint_content(combined_pattern, task_description)
            if hint_content:
                metadata = HintMetadata(
                    title=f"Success Pattern for {skill_name}",
                    category=HintCategory.SUCCESS_PATTERN,
                    skill_name=skill_name,
                    pattern_id=combined_pattern.id
                )
                
                hints.append({
                    "metadata": metadata,
                    "content": hint_content,
                    "skill_name": skill_name,
                    "category": "success_pattern"
                })
        
        return hints
    
    def _generate_failure_hints(self, patterns: List[HintPattern], 
                               task_description: str) -> List[Dict[str, Any]]:
        """Generate hints from failure patterns"""
        hints = []
        
        # Group by error type
        error_patterns = {}
        for pattern in patterns:
            error_type = self._extract_error_type(pattern)
            if error_type not in error_patterns:
                error_patterns[error_type] = []
            error_patterns[error_type].append(pattern)
        
        # Generate hints for each error type
        for error_type, error_patterns_list in error_patterns.items():
            if len(hints) >= self.max_hints_per_category:
                break
                
            combined_pattern = self._combine_patterns(error_patterns_list)
            
            hint_content = self._generate_failure_hint_content(combined_pattern, task_description)
            if hint_content:
                metadata = HintMetadata(
                    title=f"Failure Pattern: {error_type}",
                    category=HintCategory.FAILURE_PATTERN,
                    skill_name=combined_pattern.skill_name,
                    pattern_id=combined_pattern.id
                )
                
                hints.append({
                    "metadata": metadata,
                    "content": hint_content,
                    "skill_name": combined_pattern.skill_name,
                    "category": "failure_pattern"
                })
        
        return hints
    
    def _generate_best_practice_hints(self, analysis_result: ExecutionAnalysisResult,
                                     task_description: str) -> List[Dict[str, Any]]:
        """Generate best practice hints from overall analysis"""
        hints = []
        
        # Analyze overall success patterns
        if analysis_result.skill_insights:
            overall_insights = analysis_result.skill_insights.get("overall", {})
            per_skill_insights = analysis_result.skill_insights.get("per_skill", {})
            
            # Generate overall best practices
            overall_hint = self._generate_overall_best_practices(overall_insights, per_skill_insights, task_description)
            if overall_hint:
                metadata = HintMetadata(
                    title="Overall Best Practices",
                    category=HintCategory.BEST_PRACTICE,
                    skill_name="general"
                )
                
                hints.append({
                    "metadata": metadata,
                    "content": overall_hint,
                    "skill_name": "general",
                    "category": "best_practice"
                })
            
            # Generate skill-specific best practices
            for skill_name, skill_stats in per_skill_insights.items():
                if len(hints) >= self.max_hints_per_category:
                    break
                    
                if skill_stats["success_rate"] > 0.7:  # Only for reasonably successful skills
                    skill_hint = self._generate_skill_best_practices(skill_name, skill_stats, task_description)
                    if skill_hint:
                        metadata = HintMetadata(
                            title=f"Best Practices for {skill_name}",
                            category=HintCategory.BEST_PRACTICE,
                            skill_name=skill_name
                        )
                        
                        hints.append({
                            "metadata": metadata,
                            "content": skill_hint,
                            "skill_name": skill_name,
                            "category": "best_practice"
                        })
        
        return hints
    
    def _generate_troubleshooting_hints(self, failure_patterns: List[HintPattern],
                                       task_description: str) -> List[Dict[str, Any]]:
        """Generate troubleshooting hints"""
        hints = []
        
        if not failure_patterns:
            return hints
        
        # Group by skill for troubleshooting
        skill_failures = {}
        for pattern in failure_patterns:
            if pattern.skill_name not in skill_failures:
                skill_failures[pattern.skill_name] = []
            skill_failures[pattern.skill_name].append(pattern)
        
        # Generate troubleshooting guide for each skill
        for skill_name, failures in skill_failures.items():
            if len(hints) >= self.max_hints_per_category:
                break
                
            troubleshooting_guide = self._generate_troubleshooting_guide(skill_name, failures, task_description)
            if troubleshooting_guide:
                metadata = HintMetadata(
                    title=f"Troubleshooting Guide for {skill_name}",
                    category=HintCategory.TROUBLESHOOTING,
                    skill_name=skill_name
                )
                
                hints.append({
                    "metadata": metadata,
                    "content": troubleshooting_guide,
                    "skill_name": skill_name,
                    "category": "troubleshooting"
                })
        
        return hints
    
    def _generate_success_hint_content(self, pattern: HintPattern, task_description: str) -> Optional[str]:
        """Generate content for success pattern hint"""
        system_prompt = """You are an expert AI assistant that generates helpful hints and best practices.
        Based on successful execution patterns, create concise, actionable guidance that helps users
        achieve better results in similar situations."""
        
        user_prompt = f"""
        Task: {task_description or 'General task execution'}
        
        Success Pattern Analysis:
        - Pattern: {pattern.pattern_description}
        - Skill: {pattern.skill_name}
        - Success Rate: {pattern.success_rate:.1%}
        - Frequency: {pattern.frequency}
        - Examples: {pattern.examples[:2] if pattern.examples else 'N/A'}
        
        Generate a helpful hint that explains:
        1. What makes this pattern successful
        2. When to apply this approach
        3. Key factors for success
        4. Potential pitfalls to avoid
        
        Keep it concise (2-3 sentences) and actionable.
        """
        
        try:
            if not self.enable_llm or self.llm is None:
                # Return template-based hint when LLM is not available
                return f"Based on successful execution pattern: {pattern.pattern_description}. Try similar approaches in similar contexts."
            
            response = self.llm.generate(
                system_prompt=system_prompt,
                user_input=user_prompt
            )
            return response.raw_json.strip() if response and response.raw_json else None
        except Exception as e:
            logger.warning(f"Failed to generate success hint: {e}")
            # Fallback to template-based hint
            return f"Based on successful execution pattern: {pattern.pattern_description}. Try similar approaches in similar contexts."
    
    def _generate_failure_hint_content(self, pattern: HintPattern, task_description: str) -> Optional[str]:
        """Generate content for failure pattern hint"""
        system_prompt = """You are an expert AI assistant that helps users learn from failures.
        Based on failure patterns, create helpful guidance that prevents similar issues."""
        
        user_prompt = f"""
        Task: {task_description or 'General task execution'}
        
        Failure Pattern Analysis:
        - Pattern: {pattern.pattern_description}
        - Skill: {pattern.skill_name}
        - Failure Examples: {pattern.examples[:2] if pattern.examples else 'N/A'}
        - Anti-examples: {pattern.anti_examples[:2] if pattern.anti_examples else 'N/A'}
        
        Generate a helpful hint that explains:
        1. What typically goes wrong in this situation
        2. How to avoid or fix this issue
        3. Alternative approaches to consider
        4. Warning signs to watch for
        
        Keep it concise (2-3 sentences) and constructive.
        """
        
        try:
            response = self.llm.generate(
                system_prompt=system_prompt,
                user_input=user_prompt
            )
            return response.raw_json.strip() if response and response.raw_json else None
        except Exception as e:
            logger.warning(f"Failed to generate failure hint: {e}")
            return None
    
    def _generate_overall_best_practices(self, overall_insights: Dict[str, Any],
                                        per_skill_insights: Dict[str, Any],
                                        task_description: str) -> Optional[str]:
        """Generate overall best practices"""
        system_prompt = """You are an expert AI assistant that provides strategic guidance.
        Based on execution analysis, create high-level best practices for task execution."""
        
        user_prompt = f"""
        Task: {task_description or 'General task execution'}
        
        Overall Performance:
        - Total Executions: {overall_insights.get('total_executions', 0)}
        - Success Rate: {overall_insights.get('success_rate', 0):.1%}
        
        Skill Performance:
        {json.dumps(per_skill_insights, indent=2, ensure_ascii=False)}
        
        Generate 3-5 high-level best practices that apply across different skills and situations.
        Focus on strategic principles rather than specific techniques.
        """
        
        try:
            response = self.llm.generate(
                system_prompt=system_prompt,
                user_input=user_prompt
            )
            return response.raw_json.strip() if response and response.raw_json else None
        except Exception as e:
            logger.warning(f"Failed to generate overall best practices: {e}")
            return None
    
    def _generate_skill_best_practices(self, skill_name: str, skill_stats: Dict[str, Any],
                                      task_description: str) -> Optional[str]:
        """Generate skill-specific best practices"""
        system_prompt = """You are an expert AI assistant specializing in skill optimization.
        Based on skill performance data, create targeted best practices for optimal usage."""
        
        user_prompt = f"""
        Task: {task_description or 'General task execution'}
        Skill: {skill_name}
        
        Performance Data:
        - Success Rate: {skill_stats.get('success_rate', 0):.1%}
        - Total Executions: {skill_stats.get('total_executions', 0)}
        - Sample Commands: {skill_stats.get('sample_commands', [])[:2]}
        
        Generate 2-3 skill-specific best practices that help users get the most from this skill.
        Focus on when and how to use this skill effectively.
        """
        
        try:
            response = self.llm.generate(
                system_prompt=system_prompt,
                user_input=user_prompt
            )
            return response.raw_json.strip() if response and response.raw_json else None
        except Exception as e:
            logger.warning(f"Failed to generate skill best practices: {e}")
            return None
    
    def _generate_troubleshooting_guide(self, skill_name: str, failures: List[HintPattern],
                                       task_description: str) -> Optional[str]:
        """Generate troubleshooting guide for a skill"""
        system_prompt = """You are an expert troubleshooter who helps users resolve issues efficiently.
        Create practical troubleshooting guidance based on common failure patterns."""
        
        failure_descriptions = [f.pattern_description for f in failures[:3]]
        
        user_prompt = f"""
        Task: {task_description or 'General task execution'}
        Skill: {skill_name}
        
        Common Failure Patterns:
        {chr(10).join(f'- {desc}' for desc in failure_descriptions)}
        
        Create a troubleshooting guide with:
        1. Common symptoms and their likely causes
        2. Step-by-step diagnostic approach
        3. Quick fixes for typical issues
        4. When to escalate or try alternative approaches
        
        Keep it practical and actionable.
        """
        
        try:
            response = self.llm.generate(
                system_prompt=system_prompt,
                user_input=user_prompt
            )
            return response.raw_json.strip() if response and response.raw_json else None
        except Exception as e:
            logger.warning(f"Failed to generate troubleshooting guide: {e}")
            return None
    
    def _combine_patterns(self, patterns: List[HintPattern]) -> HintPattern:
        """Combine multiple similar patterns into one"""
        if not patterns:
            return HintPattern()
        
        # Use the first pattern as base
        base_pattern = patterns[0]
        
        # Combine attributes
        combined_examples = []
        combined_anti_examples = []
        total_frequency = 0
        weighted_success_rate = 0.0
        
        for pattern in patterns:
            combined_examples.extend(pattern.examples[:2])  # Take top 2 examples from each
            combined_anti_examples.extend(pattern.anti_examples[:2])
            total_frequency += pattern.frequency
            weighted_success_rate += pattern.success_rate * pattern.frequency
        
        # Remove duplicates and limit size
        combined_examples = list(dict.fromkeys(combined_examples))[:5]
        combined_anti_examples = list(dict.fromkeys(combined_anti_examples))[:3]
        
        avg_success_rate = weighted_success_rate / total_frequency if total_frequency > 0 else 0
        
        # Handle multi-skill patterns
        combined_skill_name = base_pattern.skill_name
        if ',' in base_pattern.skill_name:
            # For multi-skill patterns, use "general" as the skill name
            # but preserve the original skill names in the description
            combined_skill_name = "general"
            original_description = base_pattern.pattern_description
            skill_names = base_pattern.skill_name.split(',')
            pattern_description = f"Multi-skill pattern ({', '.join(skill_names)}) from {len(patterns)} similar executions"
        else:
            pattern_description = f"Combined pattern from {len(patterns)} similar executions"
        
        return HintPattern(
            category=base_pattern.category,
            skill_name=combined_skill_name,
            pattern_description=pattern_description,
            context_keywords=base_pattern.context_keywords,
            success_rate=avg_success_rate,
            frequency=total_frequency,
            confidence=min(1.0, total_frequency / 20.0),
            examples=combined_examples,
            anti_examples=combined_anti_examples
        )
    
    def _extract_error_type(self, pattern: HintPattern) -> str:
        """Extract error type from pattern description"""
        desc = pattern.pattern_description.lower()
        if "permission" in desc:
            return "Permission Issues"
        elif "file not found" in desc or "no such file" in desc:
            return "File/Path Issues"
        elif "command not found" in desc:
            return "Command Issues"
        elif "syntax" in desc:
            return "Syntax Errors"
        elif "timeout" in desc:
            return "Timeout Issues"
        elif "connection" in desc:
            return "Connection Issues"
        else:
            return "General Errors"