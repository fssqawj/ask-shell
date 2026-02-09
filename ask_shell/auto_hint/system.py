"""Auto Hint System - Main system that orchestrates hint extraction and generation"""

from typing import List, Optional, Dict, Any
from loguru import logger
import threading
from datetime import datetime, timedelta

from ..models.types import ExecutionResult
# Import BaseSkill in functions to avoid circular import
from .types import ExecutionAnalysisResult
from .analyzer import ExecutionResultAnalyzer
from .generator import HintGenerator
from .persistence import HintPersistenceManager


class AutoHintSystem:
    """
    Main system for automatically extracting and generating hints from execution history
    
    This system orchestrates the entire process:
    1. Analyzes execution history to discover patterns
    2. Generates hints from discovered patterns
    3. Persists hints for future use
    4. Provides interface for skills to access hints
    """
    
    def __init__(self, enable_persistence: bool = True, hints_path: Optional[str] = None):
        """
        Initialize the auto hint system
        
        Args:
            enable_persistence: Whether to enable persistent storage of hints
            hints_path: Custom path for hints storage (optional)
        """
        self.enable_persistence = enable_persistence
        self.analyzer = ExecutionResultAnalyzer()
        # Initialize generator with LLM support based on persistence setting
        self.generator = HintGenerator(enable_llm=enable_persistence)
        
        if enable_persistence:
            self.persistence = HintPersistenceManager(hints_path)
        else:
            self.persistence = None
        
        # Configuration
        self.min_history_length = 5  # Minimum execution history length to trigger analysis
        self.analysis_interval = 1  # Analyze every N task completions
        self.task_completion_count = 0
        self._lock = threading.Lock()
        
        # Cache for loaded hints
        self._hints_cache = {}
        self._cache_timestamp = {}
        self.cache_ttl = timedelta(hours=1)  # Cache for 1 hour
        
        logger.info("AutoHintSystem initialized")
    
    def process_task_completion(self, history: List[ExecutionResult], 
                              skills,
                              task_description: str = "") -> bool:
        """
        Process completed task and potentially extract hints
        
        This should be called when a task completes successfully or after sufficient
        execution history has accumulated.
        
        Args:
            history: Complete execution history for the task
            skills: List of available skills
            task_description: Original task description
            
        Returns:
            bool: True if hints were generated and saved
        """
        with self._lock:
            self.task_completion_count += 1
            
            # Check if we should trigger analysis
            if not self._should_analyze(history):
                return False
            
            try:
                logger.info("Starting automatic hint extraction process...")
                
                # Step 1: Analyze execution history
                analysis_result = self.analyzer.analyze_history(history, skills)
                
                if not analysis_result.patterns:
                    logger.info("No significant patterns found in execution history")
                    return False
                
                # Step 2: Generate hints from analysis
                generated_hints = self.generator.generate_hints_from_analysis(
                    analysis_result, task_description
                )
                
                if not generated_hints:
                    logger.info("No hints generated from analysis")
                    return False
                
                # Step 3: Save hints (if persistence enabled)
                saved_count = 0
                if self.enable_persistence and self.persistence:
                    for hint_data in generated_hints:
                        if self.persistence.save_hint(hint_data):
                            saved_count += 1
                
                logger.info(f"Auto hint extraction completed: {saved_count}/{len(generated_hints)} hints saved")
                
                # Clear cache to force reload on next access
                self._clear_cache()
                
                return saved_count > 0
                
            except Exception as e:
                logger.error(f"Error during hint extraction: {e}")
                return False
    
    def get_hints_for_skill(self, skill_name: str, max_hints: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant hints for a specific skill
        
        Args:
            skill_name: Name of the skill
            max_hints: Maximum number of hints to return
            
        Returns:
            List of hint dictionaries sorted by relevance
        """
        if not self.enable_persistence or not self.persistence:
            return []
        
        # Check cache first
        cache_key = f"skill_{skill_name}"
        if self._is_cache_valid(cache_key):
            return self._hints_cache[cache_key][:max_hints]
        
        try:
            # Load hints from persistence
            hints = self.persistence.load_hints_for_skill(skill_name)
            
            # Sort by effectiveness and usage (most effective and frequently used first)
            hints.sort(key=lambda x: (
                x.get("metadata", {}).get("effectiveness_score", 0),
                x.get("metadata", {}).get("usage_count", 0)
            ), reverse=True)
            
            # Cache the results
            self._hints_cache[cache_key] = hints
            self._cache_timestamp[cache_key] = datetime.now()
            
            return hints[:max_hints]
            
        except Exception as e:
            logger.error(f"Error loading hints for skill {skill_name}: {e}")
            return []
    
    def get_all_hints(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all hints grouped by skill
        
        Returns:
            Dictionary mapping skill names to lists of hints
        """
        if not self.enable_persistence or not self.persistence:
            return {}
        
        # Check cache first
        cache_key = "all_hints"
        if self._is_cache_valid(cache_key):
            return self._hints_cache[cache_key]
        
        try:
            all_hints = self.persistence.load_all_hints()
            
            # Cache the results
            self._hints_cache[cache_key] = all_hints
            self._cache_timestamp[cache_key] = datetime.now()
            
            return all_hints
            
        except Exception as e:
            logger.error(f"Error loading all hints: {e}")
            return {}
    
    def record_hint_usage(self, hint_id: str):
        """
        Record that a hint was used
        
        Args:
            hint_id: ID of the hint that was used
        """
        if self.enable_persistence and self.persistence:
            try:
                self.persistence.update_hint_usage(hint_id)
            except Exception as e:
                logger.warning(f"Failed to record hint usage: {e}")
    
    def update_hint_effectiveness(self, hint_id: str, score: float):
        """
        Update the effectiveness score of a hint based on user feedback
        
        Args:
            hint_id: ID of the hint
            score: Effectiveness score (0.0-1.0)
        """
        if self.enable_persistence and self.persistence:
            try:
                self.persistence.update_hint_effectiveness(hint_id, score)
            except Exception as e:
                logger.warning(f"Failed to update hint effectiveness: {e}")
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the hint system
        
        Returns:
            Dictionary with system statistics
        """
        stats = {
            "enabled": self.enable_persistence,
            "task_completion_count": self.task_completion_count,
            "analysis_interval": self.analysis_interval,
            "min_history_length": self.min_history_length,
            "cache_info": {
                "cached_items": len(self._hints_cache),
                "cache_keys": list(self._hints_cache.keys())
            }
        }
        
        if self.enable_persistence and self.persistence:
            try:
                persistence_stats = self.persistence.get_hint_statistics()
                stats.update(persistence_stats)
            except Exception as e:
                logger.warning(f"Failed to get persistence statistics: {e}")
                stats["persistence_error"] = str(e)
        
        return stats
    
    def cleanup_old_hints(self, max_age_days: int = 30, min_effectiveness: float = 0.3) -> int:
        """
        Clean up old or ineffective hints
        
        Args:
            max_age_days: Maximum age in days before considering for cleanup
            min_effectiveness: Minimum effectiveness score to keep hint
            
        Returns:
            Number of hints deleted
        """
        if not self.enable_persistence or not self.persistence:
            return 0
        
        try:
            deleted_count = self.persistence.cleanup_old_hints(max_age_days, min_effectiveness)
            if deleted_count > 0:
                self._clear_cache()  # Clear cache after cleanup
            return deleted_count
        except Exception as e:
            logger.error(f"Error during hint cleanup: {e}")
            return 0
    
    def _should_analyze(self, history: List[ExecutionResult]) -> bool:
        """
        Determine if we should trigger analysis based on current state
        
        Args:
            history: Current execution history
            
        Returns:
            bool: True if analysis should be triggered
        """
        # Check minimum history length
        if len(history) < self.min_history_length:
            return False
        
        # Check analysis interval
        if self.task_completion_count % self.analysis_interval != 0:
            return False
        
        # Additional criteria could be added here:
        # - Check if there were enough failures to warrant analysis
        # - Check if task was complex enough
        # - Check time since last analysis
        
        return True
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cache entry is still valid
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            bool: True if cache is valid
        """
        if cache_key not in self._hints_cache:
            return False
        
        if cache_key not in self._cache_timestamp:
            return False
        
        cache_age = datetime.now() - self._cache_timestamp[cache_key]
        return cache_age < self.cache_ttl
    
    def _clear_cache(self):
        """Clear all cached hints"""
        self._hints_cache.clear()
        self._cache_timestamp.clear()
        logger.debug("Hints cache cleared")
    
    def enable(self):
        """Enable the auto hint system"""
        self.enable_persistence = True
        logger.info("Auto hint system enabled")
    
    def disable(self):
        """Disable the auto hint system"""
        self.enable_persistence = False
        logger.info("Auto hint system disabled")
    
    def set_analysis_interval(self, interval: int):
        """
        Set how often to perform analysis
        
        Args:
            interval: Analyze every N task completions
        """
        self.analysis_interval = max(1, interval)
        logger.info(f"Analysis interval set to {self.analysis_interval}")
    
    def set_min_history_length(self, length: int):
        """
        Set minimum history length required for analysis
        
        Args:
            length: Minimum number of execution steps
        """
        self.min_history_length = max(1, length)
        logger.info(f"Minimum history length set to {self.min_history_length}")


# Global instance
_auto_hint_system: Optional[AutoHintSystem] = None


def get_auto_hint_system(enable_persistence: bool = True) -> AutoHintSystem:
    """
    Get or create the global auto hint system instance
    
    Args:
        enable_persistence: Whether to enable persistent storage
        
    Returns:
        AutoHintSystem instance
    """
    global _auto_hint_system
    
    if _auto_hint_system is None:
        _auto_hint_system = AutoHintSystem(enable_persistence=enable_persistence)
    
    return _auto_hint_system


def initialize_auto_hint_system(enable_persistence: bool = True, hints_path: Optional[str] = None):
    """
    Initialize the global auto hint system
    
    Args:
        enable_persistence: Whether to enable persistent storage
        hints_path: Custom path for hints storage
    """
    global _auto_hint_system
    _auto_hint_system = AutoHintSystem(
        enable_persistence=enable_persistence,
        hints_path=hints_path
    )
    logger.info("Global auto hint system initialized")