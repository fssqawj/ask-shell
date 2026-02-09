"""OpenAI LLM 客户端"""

import os
import json
from typing import Optional, List, Callable
from loguru import logger
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
    
    def generate(
        self,
        system_prompt: str, 
        user_input: str, 
        stream_callback: Optional[Callable[[str], None]] = None,
        response_class=None
    ):
        """
        生成下一步命令
        
        Args:
            user_input: 用户输入的任务描述
            last_result: 上一次命令执行的结果
            stream_callback: 流式输出回调函数，接收每个 token
            history: 历史执行结果列表
            response_class: 响应类，用于直接解析JSON到指定类型
        """
        # 构建 messages from scratch for each call
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_input)    
        ]
        
        # 调用 API - 使用流式输出
        if stream_callback:
            response_text = self._generate_with_stream(messages, stream_callback, response_class)
        else:
            response_text = self._generate_without_stream(messages, response_class)
        
        # 如果指定了响应类，则直接解析并返回对象
        if response_class is not None:
            import json
            try:
                parsed_data = json.loads(response_text)
                # Handle both dict instantiation and from_dict/from_json methods
                if hasattr(response_class, 'from_dict'):
                    return response_class.from_dict(parsed_data)
                elif hasattr(response_class, 'from_json'):
                    return response_class.from_json(response_text)
                else:
                    # Assume it's a dataclass or simple class that accepts kwargs
                    return response_class(**parsed_data)
            except json.JSONDecodeError:
                # If parsing fails, return error response
                if hasattr(response_class, 'from_dict'):
                    return response_class.from_dict({"thinking": "Failed to parse LLM response as JSON", "direct_response": f"Error: Invalid JSON response from LLM: {response_text}"})
                else:
                    return response_class(thinking="Failed to parse LLM response as JSON", direct_response=f"Error: Invalid JSON response from LLM: {response_text}")
        
        # 否则返回原始的 LLMResponse
        return LLMResponse.from_json(response_text)
    
    def _generate_with_stream(self, messages, callback: Callable[[str], None], response_class) -> str:
        """使用流式输出生成响应"""
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=0.1,
            response_format={"type": "json_object"} if response_class else None,
            stream=True
        )
        
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_response += token
                callback(token)
        
        return full_response
    
    def _generate_without_stream(self, messages, response_class) -> str:
        """不使用流式输出生成响应"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=0.1,
            response_format={"type": "json_object"} if response_class else None
        )
        return response.choices[0].message.content
    