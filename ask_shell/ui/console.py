"""控制台 UI"""

from contextlib import contextmanager
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

from ..models.types import LLMResponse, ExecutionResult, TaskContext, TaskStatus


class ConsoleUI:
    """控制台用户界面"""
    
    def __init__(self):
        self.console = Console()
    
    def print_welcome(self):
        """打印欢迎信息"""
        self.console.print(Panel.fit(
            "[bold]Ask-Shell[/bold]\n"
            "用自然语言操控你的终端\n\n"
            "[dim]危险操作会提示确认: y=执行, n=跳过, e=编辑, q=退出[/dim]",
            border_style="cyan"
        ))
    
    def print_task(self, task: str):
        """打印任务描述"""
        self.console.print(Panel(task, title="[bold cyan]任务[/bold cyan]", border_style="cyan"))
    
    def print_step(self, step: int):
        """打印步骤标题"""
        self.console.print(f"\n[bold cyan]╭─[/bold cyan] [bold white]第 {step} 步[/bold white] [bold cyan]─╮[/bold cyan]")
    
    @contextmanager
    def thinking_animation(self):
        """显示思考中的动画"""
        with self.console.status("[bold blue]🤔 AI 正在思考...[/bold blue]", spinner="dots") as status:
            yield status
    
    @contextmanager
    def streaming_display(self):
        """流式显示 AI 响应的各个字段"""
        from rich.live import Live
        from rich.panel import Panel
        import json
        import re
        
        # 创建一个可变的内容容器
        class StreamingContent:
            def __init__(self):
                self.buffer = ""
                self.thinking = ""
                self.command = ""
                self.explanation = ""
                self.next_step = ""
                self.error_analysis = ""
                self.direct_response = ""
                self.needs_llm_processing = False
                
                # 记录每个字段当前已显示的长度
                self.thinking_displayed = 0
                self.command_displayed = 0
                self.explanation_displayed = 0
                self.next_step_displayed = 0
                self.error_analysis_displayed = 0
                self.direct_response_displayed = 0
            
            def add_token(self, token: str):
                """添加新的 token 并实时提取字段内容"""
                self.buffer += token
                self._extract_fields()
            
            def _extract_fields(self):
                """实时提取各个字段的内容（支持部分内容）"""
                # 提取 thinking 字段
                thinking_match = re.search(r'"thinking"\s*:\s*"((?:[^"\\]|\\.)*)', self.buffer)
                if thinking_match:
                    raw_content = thinking_match.group(1)
                    self.thinking = raw_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                
                # 提取 error_analysis 字段
                error_match = re.search(r'"error_analysis"\s*:\s*"((?:[^"\\]|\\.)*)', self.buffer)
                if error_match:
                    raw_content = error_match.group(1)
                    self.error_analysis = raw_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                
                # 提取 command 字段
                command_match = re.search(r'"command"\s*:\s*"((?:[^"\\]|\\.)*)', self.buffer)
                if command_match:
                    raw_content = command_match.group(1)
                    self.command = raw_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                
                # 提取 explanation 字段
                explanation_match = re.search(r'"explanation"\s*:\s*"((?:[^"\\]|\\.)*)', self.buffer)
                if explanation_match:
                    raw_content = explanation_match.group(1)
                    self.explanation = raw_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                
                # 提取 next_step 字段
                next_step_match = re.search(r'"next_step"\s*:\s*"((?:[^"\\]|\\.)*)', self.buffer)
                if next_step_match:
                    raw_content = next_step_match.group(1)
                    self.next_step = raw_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                
                # 提取 direct_response 字段
                direct_response_match = re.search(r'"direct_response"\s*:\s*"((?:[^"\\]|\\.)*)', self.buffer)
                if direct_response_match:
                    raw_content = direct_response_match.group(1)
                    self.direct_response = raw_content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                
                # 提取 needs_llm_processing 字段
                needs_llm_match = re.search(r'"needs_llm_processing"\s*:\s*(true|false)', self.buffer)
                if needs_llm_match:
                    self.needs_llm_processing = needs_llm_match.group(1) == 'true'
            
            def get_display(self):
                """获取显示内容 - 只显示新增的内容"""
                from rich.console import Group
                
                panels = []
                
                # 思考过程 - 实时显示新增内容
                if self.thinking:
                    panels.append(Panel(
                        f"💭 {self.thinking}",
                        title="[bold blue]💡 思考过程[/bold blue]",
                        border_style="blue",
                        padding=(1, 2)
                    ))
                
                # 直接响应 - 用于直接LLM模式
                if self.direct_response:
                    panels.append(Panel(
                        self.direct_response,
                        title="[bold cyan]💡 AI 响应[/bold cyan]",
                        border_style="cyan",
                        padding=(1, 2)
                    ))
                
                # 生成的命令 - 实时显示
                if self.command:
                    panels.append(Panel(
                        Syntax(self.command, "bash", theme="monokai", line_numbers=False, word_wrap=True),
                        title="[bold green]✨ 生成的命令[/bold green]",
                        border_style="green",
                        padding=(0, 1)
                    ))
                
                # 说明 - 实时显示
                if self.explanation:
                    panels.append(f"[dim]💬 说明: {self.explanation}[/dim]")
                
                # 下一步 - 实时显示
                if self.next_step:
                    panels.append(f"[cyan]📋 下一步: {self.next_step}[/cyan]")
                
                # 如果什么都没有，显示思考中
                if not panels:
                    panels.append(Panel(
                        "💭 思考中...",
                        title="[bold blue]💡 思考过程[/bold blue]",
                        border_style="blue",
                        padding=(1, 2)
                    ))
                
                return Group(*panels)
        
        content = StreamingContent()
        
        with Live(content.get_display(), console=self.console, refresh_per_second=30) as live:
            def update_callback(token: str):
                content.add_token(token)
                live.update(content.get_display())
            
            yield update_callback
    
    @contextmanager
    def executing_animation(self, command: str):
        """显示命令执行中的动画"""
        # 截断过长的命令用于显示
        display_cmd = command if len(command) <= 50 else command[:47] + "..."
        with self.console.status(
            f"[bold yellow]⚙️  正在执行:[/bold yellow] [dim]{display_cmd}[/dim]",
            spinner="bouncingBall"
        ) as status:
            yield status
    
    def print_response(self, response: LLMResponse, skip_all: bool = False):
        """
        打印 LLM 响应
        
        Args:
            response: LLM 响应对象
            skip_all: 是否跳过所有显示（流式显示时已经全部显示过了）
        """
        # 如果流式显示已经展示了所有内容，直接返回
        if skip_all:
            return
        
        # 思考过程
        if response.thinking:
            self.console.print(Panel(
                f"💭 {response.thinking}",
                title="[bold blue]💡 思考过程[/bold blue]",
                border_style="blue",
                padding=(1, 2)
            ))
        
        # 生成的命令 - 高亮显示
        if response.command:
            self.console.print(Panel(
                Syntax(response.command, "bash", theme="monokai", line_numbers=False, word_wrap=True),
                title="[bold green]✨ 生成的命令[/bold green]",
                border_style="green",
                padding=(0, 1)
            ))
            if response.explanation:
                self.console.print(f"[dim]💬 说明: {response.explanation}[/dim]")
        
        # 下一步计划
        if response.next_step:
            self.console.print(f"[cyan]📋 下一步: {response.next_step}[/cyan]")
    
    def print_skill_response(self, response, skip_all: bool = False):
        """
        打印技能响应（兼容SkillResponse和LLMResponse）
        
        Args:
            response: SkillResponse或LLMResponse对象
            skip_all: 是否跳过所有显示
        """
        # 技能响应和LLM响应结构兼容，直接调用print_response
        self.print_response(response, skip_all)
    
    def print_error_analysis(self, error_analysis: str):
        """打印错误分析（在执行结果之后）"""
        if error_analysis:
            self.console.print(Panel(
                f"🔍 {error_analysis}",
                title="[bold yellow]⚠️  错误分析[/bold yellow]",
                border_style="yellow",
                padding=(1, 2)
            ))
    
    def print_direct_response(self, direct_response: str):
        """打印直接LLM响应（用于翻译、总结、分析等任务）"""
        if direct_response:
            # 使用 Markdown 渲染以支持格式化
            md = Markdown(direct_response)
            self.console.print(Panel(
                md,
                title="[bold cyan]💡 AI 响应[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            ))
    
    def print_result(self, result: ExecutionResult):
        """打印执行结果"""
        if result.success:
            style = "green"
            title = "✅ 执行成功"
            icon = "✓"
        else:
            style = "red"
            title = "❌ 执行失败"
            icon = "✗"
        
        output = result.output
        if output and output != "(无输出)":
            # 截断过长的输出
            if len(output) > 1500:
                output = output[:1500] + "\n...(输出已截断)"
            self.console.print(Panel(
                output,
                title=f"[bold {style}]{title}[/bold {style}]",
                border_style=style,
                padding=(1, 2)
            ))
        else:
            self.console.print(f"[{style}]{icon} {title} (无输出)[/{style}]")
    
    def print_complete(self):
        """打印任务完成"""
        self.console.print("\n[bold green]🎉 任务完成![/bold green]")
    
    def print_cancelled(self):
        """打印任务取消"""
        self.console.print("[yellow]🛑 用户中止任务[/yellow]")
    
    def print_max_iterations(self, max_iter: int):
        """打印达到最大迭代次数"""
        self.console.print(f"[red]⏱️  达到最大迭代次数 ({max_iter})，任务终止[/red]")
    
    def print_error(self, message: str):
        """打印错误信息"""
        self.console.print(f"[red]❌ 错误: {message}[/red]")
    
    def print_warning(self, message: str):
        """打印警告信息"""
        self.console.print(f"[yellow]⚠️  {message}[/yellow]")
    
    def print_info(self, message: str):
        """打印信息"""
        self.console.print(f"[dim]ℹ️  {message}[/dim]")
    
    def print_danger_warning(self, reason: str):
        """打印危险操作警告"""
        warning_msg = "[bold red]⚠️  警告: 检测到危险操作![/bold red]"
        if reason:
            warning_msg += f"\n\n🔍 原因: {reason}"
        warning_msg += "\n\n[dim]请确认是否执行:\n  [green]y[/green] = 执行  [yellow]n[/yellow] = 跳过  [cyan]e[/cyan] = 编辑  [red]q[/red] = 退出[/dim]"
        self.console.print(Panel(warning_msg, border_style="red", padding=(1, 2)))
    
    def prompt_action(self) -> str:
        """提示用户选择操作"""
        return Prompt.ask(
            "➤ 选择操作",
            choices=["y", "n", "e", "q"],
            default="y"
        )
    
    def prompt_edit_command(self, default: str) -> str:
        """提示用户编辑命令"""
        return Prompt.ask("✏️  编辑命令", default=default)
    
    def prompt_task(self) -> str:
        """提示用户输入任务"""
        return Prompt.ask("\n[bold cyan]➤ Ask-Shell[/bold cyan]")
    
    def print_summary(self, context: TaskContext):
        """打印任务摘要"""
        table = Table(title="任务摘要")
        table.add_column("项目", style="cyan")
        table.add_column("值", style="white")
        
        table.add_row("总步数", str(context.iteration))
        table.add_row("成功命令", str(sum(1 for r in context.history if r.success)))
        table.add_row("失败命令", str(sum(1 for r in context.history if not r.success)))
        table.add_row("状态", context.status.value)
        
        self.console.print(table)
    
    @contextmanager
    def skill_selection_animation(self):
        """显示技能选择中的动画"""
        with self.console.status("[bold magenta]🎯 正在分析任务并选择技能...[/bold magenta]", spinner="dots") as status:
            yield status
    
    def print_skill_selected(self, skill_name: str, confidence: float, reasoning: str, capabilities: list):
        """
        打印技能选择结果（使用 Rich 美化）
        
        Args:
            skill_name: 选中的技能名称
            confidence: 置信度
            reasoning: 选择理由
            capabilities: 技能能力列表
        """
        from rich.table import Table
        from rich.console import Group
        
        # 创建技能信息表格
        skill_table = Table(show_header=False, box=None, padding=(0, 1))
        skill_table.add_column("Label", style="dim")
        skill_table.add_column("Value")
        
        # 添加技能信息
        skill_table.add_row("技能", f"[bold cyan]{skill_name}[/bold cyan]")
        
        # 置信度显示（带颜色）
        if confidence >= 0.9:
            confidence_str = f"[bold green]{confidence:.0%}[/bold green]"
        elif confidence >= 0.7:
            confidence_str = f"[bold yellow]{confidence:.0%}[/bold yellow]"
        else:
            confidence_str = f"[bold red]{confidence:.0%}[/bold red]"
        skill_table.add_row("置信度", confidence_str)
        
        # 能力列表
        capabilities_str = ", ".join([f"[dim]{c}[/dim]" for c in capabilities])
        skill_table.add_row("能力", capabilities_str)
        
        # 创建理由面板
        reasoning_panel = Panel(
            f"[italic]{reasoning}[/italic]",
            title="[bold]💭 选择理由[/bold]",
            border_style="dim",
            padding=(0, 2)
        )
        
        # 组合显示
        content = Group(
            skill_table,
            "",
            reasoning_panel
        )
        
        # 使用 Panel 包装整体
        self.console.print(Panel(
            content,
            title="[bold magenta]🎯 技能选择结果[/bold magenta]",
            border_style="magenta",
            padding=(1, 2)
        ))

