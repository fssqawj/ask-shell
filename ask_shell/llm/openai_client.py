"""OpenAI LLM 客户端"""

import os
import json
from typing import Optional, List, Callable

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
        stream_callback: Optional[Callable[[str], None]] = None,
        history: Optional[List[ExecutionResult]] = None
    ) -> LLMResponse:
        """
        生成下一步命令
        
        Args:
            user_input: 用户输入的任务描述
            last_result: 上一次命令执行的结果
            stream_callback: 流式输出回调函数，接收每个 token
            history: 历史执行结果列表
        """
        # 初始化系统消息
        if not self.messages:
            self.messages.append(Message(role="system", content=self.system_prompt))
        
        # 构建用户消息
        if history:
            content = self._build_full_history_message(history, user_input, last_result)
        elif last_result:
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
    
    def _build_full_history_message(self, history: List[ExecutionResult], user_input: str, last_result: Optional[ExecutionResult] = None) -> str:
        """
        构建完整的执行历史消息
        
        Args:
            history: 历史执行结果列表
            user_input: 用户输入的任务描述
            last_result: 最后一次执行结果（与history[-1]通常是相同的，但为了兼容性传入）
        """
        history_str = "任务执行历史:\n"
        
        for i, result in enumerate(history):
            status = "成功" if result.success else "失败"
            
            # 智能判断是否需要更多内容：基于输出长度和内容类型
            # 如果输出较短或包含结构化数据，使用完整内容；否则截断
            output = result.get_output_for_llm()  # 默认使用完整内容以提供更多信息
            
            history_str += f"\n第{i+1}步 - 命令执行{status}：\n"
            history_str += f"命令: {result.command}\n"
            history_str += f"返回码: {result.returncode}\n"
            history_str += f"输出:\n{output}\n"
        
        # 添加当前任务和最新结果
        if last_result:
            status = "成功" if last_result.success else "失败"
            
            # 总是使用完整输出以提供最多信息给LLM
            output = last_result.get_output_for_llm()  # 使用完整内容
            
            current_result = f"\n最新的执行结果:\n\n命令: {last_result.command}\n返回码: {last_result.returncode}\n输出:\n{output}\n\n请根据完整的执行历史决定下一步操作。如果任务已完成，设置 is_complete 为 true。"
        else:
            current_result = f"\n请根据以上历史执行情况决定下一步操作。如果任务已完成，设置 is_complete 为 true。"
        
        return f"{history_str}{current_result}"
    
    def _generate_without_stream(self) -> str:
        """不使用流式输出生成响应"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in self.messages],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    
    def chat(
        self,
        messages: list,
        stream_callback: Optional[Callable[[str], None]] = None,
        temperature: float = 0.1,
        response_format: Optional[dict] = None,
        history: Optional[List[ExecutionResult]] = None
    ) -> str:
        """
        通用聊天方法，用于自定义消息和参数
        
        Args:
            messages: 消息列表，格式 [{"role": "system", "content": "..."}]
            stream_callback: 流式输出回调函数
            temperature: 温度参数
            response_format: 响应格式配置
            history: 历史执行结果列表（可选）
        
        Returns:
            str: LLM 响应文本
        """
        # 默认使用 JSON 格式
        if response_format is None:
            response_format = {"type": "json_object"}
        
        if stream_callback:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                response_format=response_format,
                stream=True
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_response += token
                    stream_callback(token)
            
            return full_response
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                response_format=response_format
            )
            return response.choices[0].message.content
