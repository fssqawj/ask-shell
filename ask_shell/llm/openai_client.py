"""OpenAI LLM 客户端"""

import os
import json
from typing import Optional

from openai import OpenAI

from .base import BaseLLMClient
from ..models.types import LLMResponse, ExecutionResult, Message


class OpenAIClient(BaseLLMClient):
    """OpenAI API 客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        super().__init__()
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_API_BASE")
        )
        self.model = model or os.getenv("MODEL_NAME", "gpt-4")
    
    def generate(self, user_input: str, last_result: Optional[ExecutionResult] = None) -> LLMResponse:
        """生成下一步命令"""
        # 初始化系统消息
        if not self.messages:
            self.messages.append(Message(role="system", content=self.SYSTEM_PROMPT))
        
        # 构建用户消息
        if last_result:
            content = self._build_result_message(last_result)
        else:
            content = self._build_task_message(user_input)
        
        self.messages.append(Message(role="user", content=content))
        
        # 调用 API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in self.messages],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        assistant_content = response.choices[0].message.content
        self.messages.append(Message(role="assistant", content=assistant_content))
        
        # 解析响应
        try:
            data = json.loads(assistant_content)
            return LLMResponse.from_dict(data)
        except json.JSONDecodeError:
            return LLMResponse(
                thinking="无法解析 LLM 响应",
                command="",
                explanation=assistant_content,
                is_complete=True
            )
