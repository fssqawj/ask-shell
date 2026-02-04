"""Ask-Shell 核心逻辑"""

from dataclasses import dataclass, field
from typing import Optional, List

from .models.types import TaskStatus, ExecutionResult
from .executor.shell import ShellExecutor
from .ui.console import ConsoleUI
from .skills import SkillManager, CommandSkill, DirectLLMSkill, PPTSkill, ImageSkill, BrowserSkill, WeChatSkill, FeishuSkill
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
        direct_mode: bool = False
    ):
        """
        初始化 Agent
        
        Args:
            auto_execute: 是否自动执行命令（不需要用户确认）
            working_dir: 工作目录
            direct_mode: 是否强制使用直接LLM模式（翻译、总结等任务）
        """
        self.auto_execute = auto_execute
        self.force_direct_mode = direct_mode
        
        # 初始化组件
        self.executor = ShellExecutor(working_dir=working_dir)
        self.ui = ConsoleUI()
        
        # 添加取消标志
        self.cancelled = False
        
        # 初始化技能管理器（传递 UI）
        self.skill_manager = SkillManager(ui=self.ui)
        self._register_skills()
    
    def _register_skills(self):
        """注册所有可用技能"""
        # 注册命令生成技能（默认技能）
        command_skill = CommandSkill()
        self.skill_manager.register_skill(command_skill, is_default=True)
        
        # 将LLM客户端传递给SkillManager以支持智能选择
        if hasattr(command_skill, 'llm'):
            from .skills import SkillSelector
            self.skill_manager.skill_selector = SkillSelector(command_skill.llm)
        
        # 注册直接LLM处理技能
        direct_llm_skill = DirectLLMSkill()
        self.skill_manager.register_skill(direct_llm_skill)
        
        # 注册PPT生成技能
        ppt_skill = PPTSkill()
        self.skill_manager.register_skill(ppt_skill)
        
        # 注册图片生成技能
        image_skill = ImageSkill()
        self.skill_manager.register_skill(image_skill)
        
        # 注册浏览器自动化技能
        browser_skill = BrowserSkill()
        self.skill_manager.register_skill(browser_skill)
        
        # 注册WeChat自动化技能
        wechat_skill = WeChatSkill()
        self.skill_manager.register_skill(wechat_skill)
        
        # 注册Feishu自动化技能
        feishu_skill = FeishuSkill()
        self.skill_manager.register_skill(feishu_skill)
        
        # 这里可以继续注册更多技能
        # video_skill = VideoSkill()
        # self.skill_manager.register_skill(video_skill)
    
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
