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
    def executing_animation(self, command: str):
        """显示命令执行中的动画"""
        # 截断过长的命令用于显示
        display_cmd = command if len(command) <= 50 else command[:47] + "..."
        with self.console.status(
            f"[bold yellow]⚙️  正在执行:[/bold yellow] [dim]{display_cmd}[/dim]",
            spinner="bouncingBall"
        ) as status:
            yield status
    
    def print_response(self, response: LLMResponse):
        """打印 LLM 响应"""
        # 思考过程 - 使用更醒目的样式
        if response.thinking:
            self.console.print(Panel(
                f"💭 {response.thinking}",
                title="[bold blue]💡 思考过程[/bold blue]",
                border_style="blue",
                padding=(1, 2)
            ))
        
        # 错误分析
        if response.error_analysis:
            self.console.print(Panel(
                f"🔍 {response.error_analysis}",
                title="[bold yellow]⚠️  错误分析[/bold yellow]",
                border_style="yellow",
                padding=(1, 2)
            ))
        
        # 生成的命令 - 高亮显示
        if response.command:
            self.console.print(Panel(
                Syntax(response.command, "bash", theme="monokai", line_numbers=False),
                title="[bold green]✨ 生成的命令[/bold green]",
                border_style="green",
                padding=(0, 1)
            ))
            if response.explanation:
                self.console.print(f"[dim]💬 说明: {response.explanation}[/dim]")
        
        # 下一步计划
        if response.next_step:
            self.console.print(f"[cyan]📋 下一步: {response.next_step}[/cyan]")
    
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
