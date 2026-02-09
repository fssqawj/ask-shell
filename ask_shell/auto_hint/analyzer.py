"""Execution Result Analyzer - Analyze execution history to discover patterns"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import re
from loguru import logger

from ..models.types import ExecutionResult
# Import moved to function level to avoid circular import
from .types import HintPattern, HintCategory, ExecutionAnalysisResult


class ExecutionResultAnalyzer:
    """
    Analyzes execution history to discover patterns and extract insights
    """
    
    def __init__(self):
        self.min_frequency_threshold = 3 # Minimum frequency to consider a pattern
        self.min_confidence_threshold = 0.8  # Minimum confidence for pattern extraction
        self.success_rate_threshold = 0.8  # Threshold for successful patterns
    
    def analyze_history(self, history: List[ExecutionResult], skills) -> ExecutionAnalysisResult:
        """
        Analyze execution history and extract patterns
        
        Args:
            history: List of execution results
            skills: List of available skills
            
        Returns:
            ExecutionAnalysisResult containing discovered patterns and insights
        """
        if not history:
            return ExecutionAnalysisResult()
        
        logger.info(f"Analyzing execution history with {len(history)} steps")
        
        # Extract patterns by different dimensions
        command_patterns = self._extract_command_patterns(history)
        error_patterns = self._extract_error_patterns(history)
        success_patterns = self._extract_success_patterns(history)
        skill_usage_patterns = self._extract_skill_usage_patterns(history, skills)
        
        # Combine all patterns
        all_patterns = command_patterns + error_patterns + success_patterns + skill_usage_patterns
        
        # Filter and categorize patterns
        filtered_patterns = self._filter_patterns(all_patterns)
        success_patterns = [p for p in filtered_patterns if p.category == HintCategory.SUCCESS_PATTERN]
        failure_patterns = [p for p in filtered_patterns if p.category == HintCategory.FAILURE_PATTERN]
        
        # Generate insights
        improvement_opportunities = self._generate_improvement_opportunities(history, failure_patterns)
        skill_insights = self._generate_skill_insights(history, skills)
        
        result = ExecutionAnalysisResult(
            patterns=filtered_patterns,
            success_patterns=success_patterns,
            failure_patterns=failure_patterns,
            improvement_opportunities=improvement_opportunities,
            skill_insights=skill_insights
        )
        
        logger.info(f"Analysis complete: {len(result.patterns)} patterns discovered")
        return result
    
    def _extract_command_patterns(self, history: List[ExecutionResult]) -> List[HintPattern]:
        """Extract patterns from command execution"""
        patterns = []
        
        # Group by similar commands
        command_groups = defaultdict(list)
        
        for result in history:
            if result.command and result.skill_response:
                # Normalize command for pattern matching
                normalized_cmd = self._normalize_command(result.command)
                if normalized_cmd:
                    command_groups[normalized_cmd].append(result)
        
        # Create patterns for frequently used command types
        for cmd_pattern, results in command_groups.items():
            if len(results) >= self.min_frequency_threshold:
                success_count = sum(1 for r in results if r.success)
                success_rate = success_count / len(results)
                
                pattern = HintPattern(
                    category=HintCategory.SUCCESS_PATTERN if success_rate >= self.success_rate_threshold 
                            else HintCategory.FAILURE_PATTERN,
                    skill_name=results[0].skill_response.skill_name if results[0].skill_response else "unknown",
                    pattern_description=f"Command pattern: {cmd_pattern}",
                    context_keywords=self._extract_context_keywords(results),
                    success_rate=success_rate,
                    frequency=len(results),
                    confidence=min(1.0, len(results) / 10.0),  # Normalize confidence
                    examples=[r.command for r in results[:3]],  # First 3 examples
                    anti_examples=[r.command for r in results if not r.success][:3]  # First 3 failures
                )
                patterns.append(pattern)
        
        return patterns
    
    def _extract_error_patterns(self, history: List[ExecutionResult]) -> List[HintPattern]:
        """Extract patterns from error messages"""
        patterns = []
        error_groups = defaultdict(list)
        
        for result in history:
            if result.stderr and not result.success:
                # Extract error type/categories
                error_type = self._classify_error(result.stderr)
                if error_type:
                    error_groups[error_type].append(result)
        
        for error_type, results in error_groups.items():
            if len(results) >= self.min_frequency_threshold:
                pattern = HintPattern(
                    category=HintCategory.TROUBLESHOOTING,
                    skill_name=results[0].skill_response.skill_name if results[0].skill_response else "unknown",
                    pattern_description=f"Error pattern: {error_type}",
                    context_keywords=[error_type] + self._extract_context_keywords(results),
                    success_rate=0.0,  # All are failures
                    frequency=len(results),
                    confidence=min(1.0, len(results) / 5.0),
                    examples=[f"Command: {r.command}\nError: {r.stderr[:100]}" for r in results[:3]]
                )
                patterns.append(pattern)
        
        return patterns
    
    def _extract_success_patterns(self, history: List[ExecutionResult]) -> List[HintPattern]:
        """Extract patterns from successful executions"""
        patterns = []
        
        # Find successful command sequences
        success_sequences = []
        current_sequence = []
        
        for result in history:
            if result.success:
                current_sequence.append(result)
            else:
                if len(current_sequence) >= 2:  # At least 2 consecutive successes
                    success_sequences.append(current_sequence)
                current_sequence = []
        
        # Don't forget the last sequence
        if len(current_sequence) >= 2:
            success_sequences.append(current_sequence)
        
        # Create patterns from successful sequences
        for i, sequence in enumerate(success_sequences):
            if len(sequence) >= 2:
                skill_names = [r.skill_response.skill_name for r in sequence if r.skill_response]
                unique_skills = list(set(skill_names))
                
                pattern = HintPattern(
                    category=HintCategory.SUCCESS_PATTERN,
                    skill_name=",".join(unique_skills) if unique_skills else "unknown",
                    pattern_description=f"Successful execution sequence #{i+1}",
                    context_keywords=self._extract_context_keywords(sequence),
                    success_rate=1.0,
                    frequency=1,
                    confidence=0.9,
                    examples=[f"Step {j+1}: {r.command}" for j, r in enumerate(sequence)]
                )
                patterns.append(pattern)
        
        return patterns
    
    def _extract_skill_usage_patterns(self, history: List[ExecutionResult], skills) -> List[HintPattern]:
        """Extract patterns related to skill usage"""
        patterns = []
        
        # Analyze skill selection patterns
        skill_selection_counts = defaultdict(int)
        for result in history:
            if result.skill_response and result.skill_response.skill_name:
                skill_selection_counts[result.skill_response.skill_name] += 1
        
        # Create patterns for frequently selected skills
        for skill_name, count in skill_selection_counts.items():
            if count >= self.min_frequency_threshold:
                # Get examples for this skill
                skill_examples = [
                    r for r in history 
                    if r.skill_response and r.skill_response.skill_name == skill_name
                ]
                
                success_count = sum(1 for r in skill_examples if r.success)
                success_rate = success_count / len(skill_examples) if skill_examples else 0
                
                pattern = HintPattern(
                    category=HintCategory.SUCCESS_PATTERN if success_rate >= self.success_rate_threshold 
                            else HintCategory.FAILURE_PATTERN,
                    skill_name=skill_name,
                    pattern_description=f"Frequent use of {skill_name} skill",
                    context_keywords=[skill_name, "skill_selection"],
                    success_rate=success_rate,
                    frequency=count,
                    confidence=min(1.0, count / 8.0),
                    examples=[r.command for r in skill_examples[:3]]
                )
                patterns.append(pattern)
        
        return patterns
    
    def _filter_patterns(self, patterns: List[HintPattern]) -> List[HintPattern]:
        """Filter patterns based on confidence and frequency thresholds"""
        filtered = []
        for pattern in patterns:
            if (pattern.frequency >= self.min_frequency_threshold and 
                pattern.confidence >= self.min_confidence_threshold):
                filtered.append(pattern)
        return filtered
    
    def _generate_improvement_opportunities(self, history: List[ExecutionResult], 
                                          failure_patterns: List[HintPattern]) -> List[str]:
        """Generate improvement opportunities based on failure analysis"""
        opportunities = []
        
        # Analyze common failure types
        if failure_patterns:
            opportunities.append("Identify and address common failure patterns in execution")
        
        # Check for repeated failures
        consecutive_failures = 0
        max_consecutive_failures = 0
        for result in history:
            if not result.success:
                consecutive_failures += 1
                max_consecutive_failures = max(max_consecutive_failures, consecutive_failures)
            else:
                consecutive_failures = 0
        
        if max_consecutive_failures > 2:
            opportunities.append(f"Address pattern of {max_consecutive_failures} consecutive failures")
        
        # Check for skill diversity
        skill_names = [
            r.skill_response.skill_name for r in history 
            if r.skill_response and r.skill_response.skill_name
        ]
        unique_skills = set(skill_names)
        if len(unique_skills) == 1 and len(history) > 3:
            opportunities.append("Consider using different skills for better task distribution")
        
        return opportunities
    
    def _generate_skill_insights(self, history: List[ExecutionResult], 
                                skills) -> Dict[str, Any]:
        """Generate insights about skill performance"""
        insights = {}
        
        # Overall statistics
        total_executions = len(history)
        successful_executions = sum(1 for r in history if r.success)
        success_rate = successful_executions / total_executions if total_executions > 0 else 0
        
        insights["overall"] = {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": success_rate
        }
        
        # Per-skill statistics
        skill_stats = defaultdict(lambda: {"total": 0, "success": 0, "commands": []})
        for result in history:
            if result.skill_response and result.skill_response.skill_name:
                skill_name = result.skill_response.skill_name
                skill_stats[skill_name]["total"] += 1
                if result.success:
                    skill_stats[skill_name]["success"] += 1
                skill_stats[skill_name]["commands"].append(result.command)
        
        insights["per_skill"] = {
            skill: {
                "total_executions": stats["total"],
                "success_rate": stats["success"] / stats["total"] if stats["total"] > 0 else 0,
                "sample_commands": stats["commands"][:3]
            }
            for skill, stats in skill_stats.items()
        }
        
        return insights
    
    def _normalize_command(self, command: str) -> Optional[str]:
        """Normalize command for pattern matching"""
        if not command.strip():
            return None
        
        # Remove specific values and keep structure
        normalized = command
        
        # Replace file paths with generic placeholder
        normalized = re.sub(r'/[^\s]*', '/PATH', normalized)
        normalized = re.sub(r'~[^\s]*', '~/PATH', normalized)
        
        # Replace specific filenames with generic placeholder
        normalized = re.sub(r'[a-zA-Z0-9_\-]+\.(txt|py|md|json|yaml|yml)', 'FILE.EXT', normalized)
        
        # Replace numbers with generic placeholder
        normalized = re.sub(r'\b\d+\b', 'NUM', normalized)
        
        # Replace URLs with generic placeholder
        normalized = re.sub(r'https?://[^\s]+', 'URL', normalized)
        
        return normalized.strip()
    
    def _classify_error(self, error_output: str) -> Optional[str]:
        """Classify error type from error output"""
        error_output = error_output.lower()
        
        # Common error classifications
        if "permission denied" in error_output:
            return "permission_error"
        elif "file not found" in error_output or "no such file" in error_output:
            return "file_not_found"
        elif "command not found" in error_output:
            return "command_not_found"
        elif "syntax error" in error_output:
            return "syntax_error"
        elif "timeout" in error_output:
            return "timeout"
        elif "connection refused" in error_output or "connection failed" in error_output:
            return "connection_error"
        elif "invalid" in error_output:
            return "invalid_input"
        elif "memory" in error_output:
            return "memory_error"
        else:
            return None
    
    def _extract_context_keywords(self, results: List[ExecutionResult]) -> List[str]:
        """Extract context keywords from execution results"""
        keywords = []
        
        for result in results:
            # Extract from command
            if result.command:
                # Extract command verbs
                words = result.command.lower().split()
                keywords.extend([w for w in words if len(w) > 3])
            
            # Extract from skill name
            if result.skill_response and result.skill_response.skill_name:
                keywords.append(result.skill_response.skill_name.lower())
            
            # Extract from thinking/output
            if result.skill_response and hasattr(result.skill_response, 'thinking') and result.skill_response.thinking:
                thinking_words = result.skill_response.thinking.lower().split()
                keywords.extend([w for w in thinking_words if len(w) > 4])
        
        # Remove duplicates and common words
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        unique_keywords = list(set(k for k in keywords if k not in common_words))
        
        return unique_keywords[:10]  # Limit to top 10 keywords