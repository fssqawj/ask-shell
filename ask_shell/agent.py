"""Ask-Shell 核心逻辑"""

from typing import Optional

from .models.types import TaskContext, TaskStatus, ExecutionResult, LLMResponse
from .executor.shell import ShellExecutor
from .llm.base import BaseLLMClient
from .llm.openai_client import OpenAIClient
from .llm.mock import MockLLMClient
from .ui.console import ConsoleUI


class AskShell:
    """
    Ask-Shell 主类
    
    用自然语言操控你的终端，自动生成并执行 shell 命令。
    """
    
    def __init__(
        self,
        auto_execute: bool = False,
        demo_mode: bool = False,
        working_dir: Optional[str] = None
    ):
        """
        初始化 Agent
        
        Args:
            auto_execute: 是否自动执行命令（不需要用户确认）
            demo_mode: 是否使用演示模式（不需要 API Key）
            working_dir: 工作目录
        """
        self.auto_execute = auto_execute
        
        # 初始化组件
        self.executor = ShellExecutor(working_dir=working_dir)
        self.llm: BaseLLMClient = MockLLMClient() if demo_mode else OpenAIClient()
        self.ui = ConsoleUI()
    
    def run(self, task: str) -> TaskContext:
        """
        执行任务
        
        Args:
            task: 任务描述
            
        Returns:
            TaskContext: 任务执行上下文
        """
        # 初始化任务上下文
        context = TaskContext(task_description=task)
        context.status = TaskStatus.RUNNING
        
        # 显示任务
        self.ui.print_task(task)
        
        # 重置 LLM 对话历史
        self.llm.reset()
        
        # 主循环：不断与 LLM 交互直到任务完成
        while context.status == TaskStatus.RUNNING:
            context.iteration += 1
            self.ui.print_step(context.iteration)
            
            # 调用 LLM 生成下一步命令
            try:
                with self.ui.thinking_animation():
                    response = self.llm.generate(task, context.last_result)
            except Exception as e:
                self.ui.print_error(f"LLM 调用失败: {e}")
                context.status = TaskStatus.FAILED
                break
            
            # 显示 LLM 响应
            self.ui.print_response(response)
            
            # 检查任务是否完成
            if response.is_complete:
                context.status = TaskStatus.COMPLETED
                self.ui.print_complete()
                break
            
            # 获取要执行的命令
            command = response.command.strip() if response.command else ""
            if not command:
                self.ui.print_warning("没有生成命令，跳过...")
                continue
            
            # 处理用户确认（只有危险操作才需要确认）
            action = self._handle_user_confirmation(command, response)
            
            if action == "quit":
                context.status = TaskStatus.CANCELLED
                self.ui.print_cancelled()
                break
            elif action == "skip":
                # 跳过时，告诉 LLM 用户选择跳过
                skip_result = ExecutionResult(
                    command=command,
                    returncode=-1,
                    stdout="",
                    stderr="用户选择跳过此命令，请尝试其他方法"
                )
                context.add_result(skip_result)
                continue
            elif action.startswith("edit:"):
                command = action[5:]
            
            # 执行命令
            with self.ui.executing_animation(command):
                result = self.executor.execute(command)
            context.add_result(result)
            
            # 显示执行结果
            self.ui.print_result(result)
        
        return context
    
    def _handle_user_confirmation(self, command: str, response: LLMResponse) -> str:
        """
        处理用户确认（只有危险操作才需要确认）
        
        Args:
            command: 待执行的命令
            response: LLM 响应（包含危险判断）
            
        Returns:
            str: 操作指令
                - "execute": 执行
                - "skip": 跳过
                - "quit": 退出
                - "edit:xxx": 编辑后的命令
        """
        # 如果是自动执行模式，直接执行
        if self.auto_execute:
            return "execute"
        
        # 如果不是危险操作，直接执行
        if not response.is_dangerous:
            return "execute"
        
        # 危险操作，显示警告并要求确认
        self.ui.print_danger_warning(response.danger_reason)
        choice = self.ui.prompt_action()
        
        if choice == "q":
            return "quit"
        elif choice == "n":
            return "skip"
        elif choice == "e":
            edited = self.ui.prompt_edit_command(command)
            return f"edit:{edited}"
        else:  # "y"
            return "execute"
    
    def run_interactive(self):
        """运行交互模式"""
        self.ui.print_welcome()
        
        while True:
            try:
                task = self.ui.prompt_task()
                if task.lower() in ["exit", "quit", "q"]:
                    break
                if task.strip():
                    context = self.run(task)
                    # 可选：显示任务摘要
                    # self.ui.print_summary(context)
            except KeyboardInterrupt:
                self.ui.console.print("\n[yellow]再见![/yellow]")
                break
