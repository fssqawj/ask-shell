"""Ask-Shell 核心逻辑"""

from typing import Optional
from loguru import logger

from .models.types import TaskStatus, ExecutionResult
from .executor.shell import ShellExecutor
from .ui.console import ConsoleUI
from .skills import SkillManager
from .context.task_context import TaskContext

class AskShell:
    """
    Ask-Shell 主类
    
    用自然语言操控你的终端，使用AI技能系统完成各种任务。
    """
    
    def __init__(
        self,
        auto_execute: bool = False,
        working_dir: Optional[str] = None,
        direct_mode: bool = False,
        enable_persistence: bool = True
    ):
        """
        初始化 Agent
        
        Args:
            auto_execute: 是否自动执行命令（不需要用户确认）
            working_dir: 工作目录
            direct_mode: 是否强制使用直接LLM模式（翻译、总结等任务）
            enable_persistence: 是否启用技能持久化
        """
        self.auto_execute = auto_execute
        self.force_direct_mode = direct_mode
        
        # 初始化组件
        self.executor = ShellExecutor(working_dir=working_dir)
        self.ui = ConsoleUI()
        
        # 添加取消标志
        self.cancelled = False
        
        # 初始化技能管理器（传递 UI 和 persistence 配置）
        self.skill_manager = SkillManager(ui=self.ui, enable_persistence=enable_persistence)
    
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
        
        # 重置取消标志
        self.cancelled = False
        
        # 显示任务
        self.ui.print_task(task)
        
        # 重置技能状态
        self.skill_manager.reset_all()
        
        # 执行任务使用技能系统
        return self._run_with_skills(task, context)
    
    def _run_with_skills(self, task: str, context: TaskContext) -> TaskContext:
        """
        使用技能系统运行任务
        
        Args:
            task: 任务描述
            context: 任务上下文
            
        Returns:
            TaskContext: 任务执行上下文
        """
        # Track skill responses for context
        
        # 主循环：不断调用技能直到任务完成
        while context.status == TaskStatus.RUNNING:
            # 检查是否被取消
            if self.cancelled:
                context.status = TaskStatus.CANCELLED
                self.skill_manager.reset_all()
                self.ui.print_cancelled()
                break
                
            context.iteration += 1
            self.ui.print_step(context.iteration)
            
            # 准备上下文
            skill_context = {
                'last_result': context.last_result,
                'iteration': context.iteration,
                'history': context.history,
                'memory_bank': context.memory_bank,
            }
            
            # 使用技能管理器执行任务
            try:
                response = self.skill_manager.execute(
                    task,
                    context=skill_context,
                )
            except Exception as e:
                self.ui.print_error(f"技能执行失败: {e}")
                context.status = TaskStatus.FAILED
                
                # Trigger auto hint learning even on failure to learn from mistakes
                self._trigger_auto_hint_learning(context, task)
                
                break
            
            # 显示响应（跳过所有字段，因为已经流式显示了）
            self.ui.print_skill_response(response, skip_all=True)
            
            # Determine if task is complete based on skill selector's assessment
            # Use task_complete field which is set by the skill selector
            task_complete = response.task_complete if response.task_complete is not None else False
            
            
            # 获取要执行的命令
            command = response.command.strip() if response.command else ""
            
            # 如果任务完成且没有命令需要执行，直接退出
            if task_complete and not command:
                context.status = TaskStatus.COMPLETED
                self.ui.print_complete()
                self.skill_manager.reset_all()
                self._trigger_auto_hint_learning(context, task)
                break
            
            # 如果没有命令，跳过
            if not command:
                self.ui.print_warning("改技能没有需要执行的命令。")
                context.add_result(ExecutionResult(command="", returncode=0, stdout="", stderr="改技能没有需要执行的命令", skill_response=response))
                continue
            
            # 处理用户确认（只有危险操作才需要确认）
            action = self._handle_user_confirmation(command, response)
            
            if action == "quit":
                context.status = TaskStatus.CANCELLED
                self.ui.print_cancelled()
                
                # Trigger auto hint learning even on cancellation to capture partial learning
                self._trigger_auto_hint_learning(context, task)
                
                break
            elif action == "skip":
                # 跳过时，告诉技能用户选择跳过
                skip_result = ExecutionResult(
                    command=command,
                    returncode=-1,
                    stdout="",
                    stderr="用户选择跳过此命令，请尝试其他方法",
                    skill_response=response
                )
                context.add_result(skip_result)
                continue
            elif action.startswith("edit:"):
                command = action[5:]
            
            # 执行命令
            with self.ui.executing_animation(command):
                result = self.executor.execute(command)
            context.add_result(ExecutionResult(command=command, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr, skill_response=response))
            
            # 显示执行结果
            self.ui.print_result(result)
            
            # 如果有错误分析，在执行结果后显示
            if response.error_analysis:
                self.ui.print_error_analysis(response.error_analysis)
            
                # 如果任务标记为完成，在执行完最后一条命令后退出
            if task_complete:
                context.status = TaskStatus.COMPLETED
                self.ui.print_complete()
                
                # Trigger auto hint learning after successful task completion
                self._trigger_auto_hint_learning(context, task)
                
                # 任务完成后清理技能状态，特别是浏览器技能
                self.skill_manager.reset_all()
                break
        
        return context
    
    def _handle_user_confirmation(self, command: str, response) -> str:
        """
        处理用户确认（只有危险操作才需要确认）
        
        Args:
            command: 待执行的命令
            response: 技能响应（包含危险判断）
            
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
                # 用户中断时清理技能状态
                self.skill_manager.reset_all()
                self.ui.console.print("\n[yellow]再见![/yellow]")
                break
    
    def _trigger_auto_hint_learning(self, context, task_description: str):
        """
        Trigger auto hint learning after task completion
        
        Args:
            context: Task context with execution history
            task_description: Original task description
        """
        try:
            from .auto_hint import get_auto_hint_system
            auto_hint_system = get_auto_hint_system()
            
            # Only trigger learning if we have sufficient history
            if len(context.history) >= 2:
                auto_hint_system.process_task_completion(
                    context.history, 
                    self.skill_manager.skills, 
                    task_description
                )
                logger.info("Auto hint learning triggered after task completion")
            else:
                logger.info("Insufficient execution history for hint learning")
        except Exception as e:
            logger.warning(f"Failed to trigger auto hint learning: {e}")
