"""OpenAI LLM 客户端"""

import os
import json
from typing import Optional, Callable

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
        user_input: str, 
        last_result: Optional[ExecutionResult] = None,
        stream_callback: Optional[Callable[[str], None]] = None
    ) -> LLMResponse:
        """
        生成下一步命令
        
        Args:
            user_input: 用户输入的任务描述
            last_result: 上一次命令执行的结果
            stream_callback: 流式输出回调函数，接收每个 token
        """
        # 初始化系统消息
        if not self.messages:
            self.messages.append(Message(role="system", content=self.system_prompt))
        
        # 构建用户消息
        if last_result:
            content = self._build_result_message(last_result, user_input)
        else:
            content = self._build_task_message(user_input)
        
        self.messages.append(Message(role="user", content=content))
        
        # 调用 API - 使用流式输出
        if stream_callback:
            response_text = self._generate_with_stream(stream_callback)
        else:
            response_text = self._generate_without_stream()
        
        self.messages.append(Message(role="assistant", content=response_text))
        
        # 解析响应
        try:
            data = json.loads(response_text)
            return LLMResponse.from_dict(data)
        except json.JSONDecodeError:
            return LLMResponse(
                thinking="无法解析 LLM 响应",
                command="",
                explanation=response_text,
                is_complete=True
            )
    
    def _generate_with_stream(self, callback: Callable[[str], None]) -> str:
        """使用流式输出生成响应"""
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in self.messages],
            temperature=0.1,
            response_format={"type": "json_object"},
            stream=True
        )
        
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_response += token
                callback(token)
        
        return full_response
    
    def _generate_without_stream(self) -> str:
        """不使用流式输出生成响应"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in self.messages],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
