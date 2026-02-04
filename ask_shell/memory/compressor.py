"""Memory Compressor - handles summarization and compression of memory entries"""

from typing import List
from .types import MemoryEntry, MemorySummary
from ..llm.openai_client import OpenAIClient
from ..models.types import Message

class MemoryCompressor:
    """
    Handles compression and summarization of memory entries using LLM
    """
    
    def __init__(self, llm_client: OpenAIClient = None):
        """
        Initialize memory compressor
        
        Args:
            llm_client: LLM client for generating summaries (optional)
        """
        self.llm_client = llm_client
    
    def compress_entries(self, entries: List[MemoryEntry], max_length: int = 500) -> MemorySummary:
        """
        Compress a list of entries into a single summary using either
        rule-based or LLM-based summarization
        
        Args:
            entries: List of entries to compress
            max_length: Maximum length of the summary
            
        Returns:
            MemorySummary containing the compressed information
        """
        if not entries:
            return MemorySummary(title="Empty Summary", content="No entries to summarize")
        
        if self.llm_client:
            return self._llm_compress(entries, max_length)
        else:
            return self._rule_based_compress(entries, max_length)
    
    def _llm_compress(self, entries: List[MemoryEntry], max_length: int = 500) -> MemorySummary:
        """
        Use LLM to generate a concise summary of multiple entries
        
        Args:
            entries: List of entries to compress
            max_length: Maximum length of the summary
            
        Returns:
            MemorySummary containing the LLM-generated summary
        """
        # Prepare the content for the LLM
        content_parts = []
        for entry in entries:
            parts = []
            if entry.thinking:
                parts.append(f"Thinking: {entry.thinking}")
            if entry.command:
                parts.append(f"Command: {entry.command}")
            if entry.result:
                parts.append(f"Result: {entry.result}")
            if parts:
                content_parts.append(f"Step {entry.step_number} ({entry.skill_name}): " + "; ".join(parts))
        
        full_content = "\n".join(content_parts)
        
        # Create a prompt for the LLM to summarize
        prompt = f"""
        请将以下多步骤执行历史总结为简洁的摘要，重点突出关键结果和重要发现：

        {full_content}

        请提供一个简短的标题和详细的内容摘要，长度不超过{max_length}个字符。
        摘要应该包含：
        1. 完成的主要任务
        2. 关键结果或发现
        3. 重要的错误或障碍（如果有）
        4. 对后续步骤可能有用的任何信息

        请按照以下JSON格式回复：
        {{
            "title": "摘要标题",
            "content": "详细摘要内容"
        }}
        """
        
        try:
            # Create messages for the LLM
            messages = [
                Message(role="system", content="You are a helpful assistant that creates concise summaries of execution histories. Respond with valid JSON."),
                Message(role="user", content=prompt)
            ]
            
            # Call the LLM to generate the summary
            completion = self.llm_client.client.chat.completions.create(
                model=self.llm_client.model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            import json
            summary_data = json.loads(response_text)
            
            return MemorySummary(
                title=summary_data.get("title", f"Summary of {len(entries)} steps"),
                content=summary_data.get("content", "Summary could not be generated"),
                source_entries=[entry.id for entry in entries],
                tags=self._extract_tags_from_entries(entries)
            )
            
        except Exception as e:
            # Fall back to rule-based compression if LLM fails
            print(f"LLM compression failed: {e}, falling back to rule-based compression")
            return self._rule_based_compress(entries, max_length)
    
    def _rule_based_compress(self, entries: List[MemoryEntry], max_length: int = 500) -> MemorySummary:
        """
        Use rule-based approach to generate summary of multiple entries
        
        Args:
            entries: List of entries to compress
            max_length: Maximum length of the summary
            
        Returns:
            MemorySummary containing the rule-based summary
        """
        # Combine key information from all entries
        content_parts = []
        
        for entry in entries:
            part = f"Step {entry.step_number} ({entry.skill_name}): {entry.summary}"
            content_parts.append(part)
        
        full_content = " | ".join(content_parts)
        
        # Truncate if too long
        if len(full_content) > max_length:
            full_content = full_content[:max_length-3] + "..."
        
        title = f"Summary of {len(entries)} steps ({entries[0].step_number}-{entries[-1].step_number})"
        
        return MemorySummary(
            title=title,
            content=full_content,
            source_entries=[entry.id for entry in entries],
            tags=self._extract_tags_from_entries(entries)
        )
    
    def _extract_tags_from_entries(self, entries: List[MemoryEntry]) -> List[str]:
        """
        Extract common tags from a list of entries
        
        Args:
            entries: List of entries to extract tags from
            
        Returns:
            List of extracted tags
        """
        all_tags = set()
        for entry in entries:
            all_tags.update(entry.tags)
        return list(all_tags)
    
    def calculate_importance(self, entry: MemoryEntry) -> float:
        """
        Calculate the importance of a memory entry based on various factors
        
        Args:
            entry: Memory entry to evaluate
            
        Returns:
            Importance score between 0.0 and 1.0
        """
        importance = 0.5  # Base importance
        
        # Increase importance for certain skill types
        high_importance_skills = ['BrowserSkill', 'CommandSkill']
        if entry.skill_name in high_importance_skills:
            importance += 0.2
        
        # Increase importance if it has results or errors
        if entry.result and ('error' in entry.result.lower() or 'fail' in entry.result.lower()):
            importance += 0.3
        elif entry.result:
            importance += 0.1
        
        # Increase importance if it has important keywords
        important_keywords = ['success', 'completed', 'created', 'found', 'important', 'key']
        combined_text = f"{entry.thinking} {entry.command} {entry.result} {entry.summary}".lower()
        for keyword in important_keywords:
            if keyword in combined_text:
                importance += 0.1
        
        # Cap importance between 0.0 and 1.0
        return min(1.0, max(0.0, importance))