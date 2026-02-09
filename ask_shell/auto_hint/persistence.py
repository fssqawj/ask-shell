"""Hint Persistence Manager - Manage storage and retrieval of generated hints"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from .types import HintMetadata, HintCategory


class HintPersistenceManager:
    """
    Manages persistence of generated hints including storage, retrieval, and versioning
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the persistence manager
        
        Args:
            base_path: Base directory for hints storage. If None, uses default path.
        """
        if base_path is None:
            # Default to skills/hints_generated directory
            base_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "skills", 
                "hints_generated"
            )
        
        self.base_path = Path(base_path)
        self.metadata_file = self.base_path / "hints_metadata.json"
        self._ensure_directories()
        self._load_metadata()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        # Create base directory
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create skill-specific directories
        skill_dirs = [
            "browser", "command", "general", "wechat", 
            "feishu", "ppt", "image", "direct_llm"
        ]
        
        for skill_dir in skill_dirs:
            (self.base_path / skill_dir).mkdir(exist_ok=True)
    
    def _load_metadata(self):
        """Load hints metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load hints metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save hints metadata to file"""
        try:
            # Convert metadata to JSON-serializable format
            def make_serializable(obj):
                if hasattr(obj, '__dict__'):
                    # Handle dataclass objects
                    result = {}
                    for k, v in obj.__dict__.items():
                        result[k] = make_serializable(v)
                    return result
                elif isinstance(obj, (list, tuple)):
                    return [make_serializable(item) for item in obj]
                elif isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}
                elif hasattr(obj, 'value') and hasattr(obj, 'name'):
                    # Handle enum objects
                    return obj.value
                elif hasattr(obj, 'isoformat'):
                    # Handle datetime objects
                    return obj.isoformat()
                else:
                    return obj
            
            serializable_metadata = make_serializable(self.metadata)
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_metadata, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Failed to save hints metadata: {e}")
    
    def save_hint(self, hint_data: Dict[str, Any]) -> bool:
        """
        Save a generated hint
        
        Args:
            hint_data: Dictionary containing hint metadata and content
            
        Returns:
            bool: True if saved successfully
        """
        logger.info(f"Saving hint: {hint_data}")
        try:
            metadata = hint_data.get("metadata")
            if not metadata:
                logger.error("Hint data missing metadata")
                return False
            
            # Convert metadata to dict if it's a dataclass
            if hasattr(metadata, '__dict__'):
                metadata_dict = metadata.__dict__.copy()  # Create a copy to avoid modifying the original
                # Convert enum fields to their values
                if 'category' in metadata_dict and hasattr(metadata_dict['category'], 'value'):
                    metadata_dict['category'] = metadata_dict['category'].value
                # Convert datetime fields to ISO format strings
                if 'created_at' in metadata_dict and hasattr(metadata_dict['created_at'], 'isoformat'):
                    metadata_dict['created_at'] = metadata_dict['created_at'].isoformat()
                if 'updated_at' in metadata_dict and hasattr(metadata_dict['updated_at'], 'isoformat'):
                    metadata_dict['updated_at'] = metadata_dict['updated_at'].isoformat()
            else:
                metadata_dict = metadata
            
            # Generate unique filename based on content hash
            # Use formatted hint data for hash generation
            hash_hint_data = {
                "metadata": metadata_dict,
                "content": hint_data.get("content", "")
            }
            content_hash = self._generate_content_hash(hash_hint_data)
            filename = f"hint_{content_hash}.md"
            
            # Determine directory based on skill
            skill_dir = self._get_skill_directory(metadata_dict.get("skill_name", "general"))
            file_path = skill_dir / filename
            
            # Create hint content
            # Create new hint_data with converted metadata
            formatted_hint_data = {
                "metadata": metadata_dict,
                "content": hint_data.get("content", "")
            }
            hint_content = self._format_hint_content(formatted_hint_data)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(hint_content)
            
            # Update metadata
            hint_id = metadata_dict.get("id", content_hash)
            self.metadata[hint_id] = {
                "id": hint_id,
                "title": metadata_dict.get("title", ""),
                "category": metadata_dict.get("category", "best_practice"),
                "skill_name": metadata_dict.get("skill_name", "general"),
                "filename": filename,
                "created_at": metadata_dict.get("created_at", datetime.now().isoformat()),
                "updated_at": datetime.now().isoformat(),
                "usage_count": metadata_dict.get("usage_count", 0),
                "effectiveness_score": metadata_dict.get("effectiveness_score", 0.0),
                "content_hash": content_hash
            }
            
            self._save_metadata()
            logger.info(f"Saved hint: {metadata_dict.get('title', 'Untitled')} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save hint: {e}")
            return False
    
    def load_hints_for_skill(self, skill_name: str) -> List[Dict[str, Any]]:
        """
        Load all hints for a specific skill
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            List of hint dictionaries
        """
        hints = []
        skill_dir = self._get_skill_directory(skill_name)
        
        if not skill_dir.exists():
            return hints
        
        # Load hints from metadata
        skill_hints = [
            meta for meta in self.metadata.values()
            if meta.get("skill_name") == skill_name
        ]
        
        # Read content for each hint
        for hint_meta in skill_hints:
            try:
                file_path = skill_dir / hint_meta["filename"]
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    hints.append({
                        "metadata": hint_meta,
                        "content": content
                    })
            except Exception as e:
                logger.warning(f"Failed to load hint {hint_meta.get('title', 'Unknown')}: {e}")
        
        return hints
    
    def load_all_hints(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load all hints grouped by skill
        
        Returns:
            Dictionary mapping skill names to lists of hints
        """
        all_hints = {}
        
        # Get all skill directories
        skill_dirs = [d for d in self.base_path.iterdir() if d.is_dir() and d.name != ".git"]
        
        for skill_dir in skill_dirs:
            skill_name = skill_dir.name
            hints = self.load_hints_for_skill(skill_name)
            if hints:
                all_hints[skill_name] = hints
        
        return all_hints
    
    def update_hint_usage(self, hint_id: str):
        """
        Update usage count for a hint
        
        Args:
            hint_id: ID of the hint to update
        """
        if hint_id in self.metadata:
            self.metadata[hint_id]["usage_count"] = self.metadata[hint_id].get("usage_count", 0) + 1
            self.metadata[hint_id]["updated_at"] = datetime.now().isoformat()
            self._save_metadata()
            logger.debug(f"Updated usage count for hint {hint_id}")
    
    def update_hint_effectiveness(self, hint_id: str, score: float):
        """
        Update effectiveness score for a hint
        
        Args:
            hint_id: ID of the hint to update
            score: Effectiveness score (0.0-1.0)
        """
        if hint_id in self.metadata:
            self.metadata[hint_id]["effectiveness_score"] = score
            self.metadata[hint_id]["updated_at"] = datetime.now().isoformat()
            self._save_metadata()
            logger.debug(f"Updated effectiveness score for hint {hint_id}: {score}")
    
    def delete_hint(self, hint_id: str) -> bool:
        """
        Delete a hint
        
        Args:
            hint_id: ID of the hint to delete
            
        Returns:
            bool: True if deleted successfully
        """
        if hint_id not in self.metadata:
            return False
        
        try:
            hint_meta = self.metadata[hint_id]
            skill_dir = self._get_skill_directory(hint_meta["skill_name"])
            file_path = skill_dir / hint_meta["filename"]
            
            # Delete file
            if file_path.exists():
                file_path.unlink()
            
            # Remove from metadata
            del self.metadata[hint_id]
            self._save_metadata()
            
            logger.info(f"Deleted hint: {hint_meta.get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete hint {hint_id}: {e}")
            return False
    
    def get_hint_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored hints
        
        Returns:
            Dictionary with statistics
        """
        total_hints = len(self.metadata)
        hints_by_skill = {}
        hints_by_category = {}
        
        for meta in self.metadata.values():
            # Count by skill
            skill = meta.get("skill_name", "unknown")
            hints_by_skill[skill] = hints_by_skill.get(skill, 0) + 1
            
            # Count by category
            category = meta.get("category", "unknown")
            hints_by_category[category] = hints_by_category.get(category, 0) + 1
        
        return {
            "total_hints": total_hints,
            "hints_by_skill": hints_by_skill,
            "hints_by_category": hints_by_category,
            "storage_path": str(self.base_path)
        }
    
    def cleanup_old_hints(self, max_age_days: int = 30, min_effectiveness: float = 0.3) -> int:
        """
        Clean up old or ineffective hints
        
        Args:
            max_age_days: Maximum age in days before considering for cleanup
            min_effectiveness: Minimum effectiveness score to keep hint
            
        Returns:
            Number of hints deleted
        """
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        to_delete = []
        for hint_id, meta in self.metadata.items():
            # Check age
            created_at = datetime.fromisoformat(meta.get("created_at", datetime.now().isoformat()))
            is_old = created_at < cutoff_date
            
            # Check effectiveness
            effectiveness = meta.get("effectiveness_score", 0.0)
            is_ineffective = effectiveness < min_effectiveness
            
            # Check usage
            usage_count = meta.get("usage_count", 0)
            is_unused = usage_count == 0
            
            # Delete if meets cleanup criteria
            if (is_old and is_ineffective) or (is_unused and is_ineffective):
                to_delete.append(hint_id)
        
        # Perform deletion
        for hint_id in to_delete:
            if self.delete_hint(hint_id):
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old/ineffective hints")
        
        return deleted_count
    
    def _get_skill_directory(self, skill_name: str) -> Path:
        """Get directory path for a skill"""
        # Map skill names to directories
        skill_mapping = {
            "BrowserSkill": "browser",
            "CommandSkill": "command", 
            "WeChatSkill": "wechat",
            "FeishuSkill": "feishu",
            "PPTSkill": "ppt",
            "ImageSkill": "image",
            "DirectLLMSkill": "direct_llm"
        }
        
        dir_name = skill_mapping.get(skill_name, "general")
        return self.base_path / dir_name
    
    def _generate_content_hash(self, hint_data: Dict[str, Any]) -> str:
        """Generate hash of hint content for unique identification"""
        content_str = json.dumps(hint_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()[:12]
    
    def _format_hint_content(self, hint_data: Dict[str, Any]) -> str:
        """Format hint data as markdown content"""
        metadata = hint_data.get("metadata", {})
        content = hint_data.get("content", "")
        
        # Create markdown header
        md_lines = []
        md_lines.append(f"# {metadata.get('title', 'Untitled Hint')}")
        md_lines.append("")
        
        # Add metadata as frontmatter-like section
        md_lines.append("## Metadata")
        md_lines.append(f"- **Category**: {metadata.get('category', 'best_practice')}")
        md_lines.append(f"- **Skill**: {metadata.get('skill_name', 'general')}")
        md_lines.append(f"- **Created**: {metadata.get('created_at', 'Unknown')}")
        md_lines.append(f"- **Usage Count**: {metadata.get('usage_count', 0)}")
        md_lines.append(f"- **Effectiveness**: {metadata.get('effectiveness_score', 0.0):.2f}")
        md_lines.append("")
        
        # Add main content
        md_lines.append("## Content")
        md_lines.append(content)
        md_lines.append("")
        
        # Add footer
        md_lines.append("---")
        md_lines.append(f"*Generated automatically from execution history on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(md_lines)