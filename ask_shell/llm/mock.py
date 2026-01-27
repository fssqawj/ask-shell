"""Mock LLM 客户端 (用于演示)"""

from typing import Optional

from .base import BaseLLMClient
from ..models.types import LLMResponse, ExecutionResult


class MockLLMClient(BaseLLMClient):
    """模拟 LLM 客户端，用于演示和测试"""
    
    def __init__(self):
        super().__init__()
        self.step = 0
        self.task_type = None
    
    def reset(self):
        super().reset()
        self.step = 0
        self.task_type = None
    
    def _detect_task_type(self, task: str) -> str:
        """检测任务类型"""
        task_lower = task.lower()
        if "创建" in task_lower or "新建" in task_lower or "mkdir" in task_lower:
            return "create"
        elif "删除" in task_lower or "rm" in task_lower:
            return "delete"
        elif "查找" in task_lower or "搜索" in task_lower or "find" in task_lower:
            return "find"
        elif "列出" in task_lower or "显示" in task_lower or "ls" in task_lower or "查看" in task_lower:
            return "list"
        elif "统计" in task_lower or "count" in task_lower or "行数" in task_lower:
            return "count"
        else:
            return "generic"
    
    def generate(self, user_input: str, last_result: Optional[ExecutionResult] = None) -> LLMResponse:
        """模拟生成命令"""
        # 首次调用时检测任务类型
        if self.task_type is None:
            self.task_type = self._detect_task_type(user_input)
        
        # 根据上一次执行结果判断
        if last_result and not last_result.success:
            self.step += 1
            return LLMResponse(
                thinking=f"上一条命令执行失败，错误信息: {last_result.stderr}。让我尝试另一种方法。",
                command="echo '演示模式: 模拟错误恢复'",
                explanation="在真实模式下，LLM 会根据错误信息调整命令",
                is_complete=False,
                next_step="根据新的执行结果继续",
                error_analysis=last_result.stderr
            )
        
        # 根据任务类型和步骤返回响应
        return self._get_response_for_task()
    
    def _get_response_for_task(self) -> LLMResponse:
        """根据任务类型获取响应"""
        handlers = {
            "create": self._handle_create,
            "list": self._handle_list,
            "find": self._handle_find,
            "count": self._handle_count,
            "delete": self._handle_delete,
            "generic": self._handle_generic,
        }
        handler = handlers.get(self.task_type, self._handle_generic)
        return handler()
    
    def _handle_create(self) -> LLMResponse:
        """处理创建任务"""
        if self.step == 0:
            self.step += 1
            return LLMResponse(
                thinking="用户想要创建文件夹。我将使用 mkdir 命令，添加 -p 参数以避免目录已存在时报错。",
                command="mkdir -p demo_folder",
                explanation="创建名为 demo_folder 的目录",
                is_complete=False,
                next_step="验证目录是否创建成功"
            )
        elif self.step == 1:
            self.step += 1
            return LLMResponse(
                thinking="目录创建命令已执行，现在验证是否成功。",
                command="ls -la | grep demo_folder",
                explanation="检查 demo_folder 是否存在",
                is_complete=False,
                next_step="确认结果后完成任务"
            )
        else:
            return LLMResponse(
                thinking="目录已成功创建并验证，任务完成。",
                is_complete=True
            )
    
    def _handle_list(self) -> LLMResponse:
        """处理列出任务"""
        if self.step == 0:
            self.step += 1
            return LLMResponse(
                thinking="用户想要列出文件。使用 ls -la 显示详细信息。",
                command="ls -la",
                explanation="列出当前目录所有文件，包括隐藏文件",
                is_complete=False,
                next_step="查看结果"
            )
        else:
            return LLMResponse(
                thinking="已成功列出文件，任务完成。",
                is_complete=True
            )
    
    def _handle_find(self) -> LLMResponse:
        """处理查找任务"""
        if self.step == 0:
            self.step += 1
            return LLMResponse(
                thinking="用户想要查找文件。使用 find 命令搜索。",
                command="find . -type f -name '*.py' 2>/dev/null | head -20",
                explanation="查找当前目录下的 Python 文件",
                is_complete=False,
                next_step="分析搜索结果"
            )
        else:
            return LLMResponse(
                thinking="搜索完成，已找到相关文件。",
                is_complete=True
            )
    
    def _handle_count(self) -> LLMResponse:
        """处理统计任务"""
        if self.step == 0:
            self.step += 1
            return LLMResponse(
                thinking="用户想要统计代码行数。先查找所有代码文件。",
                command="find . -name '*.py' -type f | head -20",
                explanation="查找所有 Python 文件",
                is_complete=False,
                next_step="统计这些文件的行数"
            )
        elif self.step == 1:
            self.step += 1
            return LLMResponse(
                thinking="找到了 Python 文件，现在统计总行数。",
                command="find . -name '*.py' -type f -exec wc -l {} + 2>/dev/null | tail -1",
                explanation="统计所有 Python 文件的总行数",
                is_complete=False,
                next_step="报告统计结果"
            )
        else:
            return LLMResponse(
                thinking="统计完成，已获得代码行数信息。",
                is_complete=True
            )
    
    def _handle_delete(self) -> LLMResponse:
        """处理删除任务"""
        if self.step == 0:
            self.step += 1
            return LLMResponse(
                thinking="删除操作需要谨慎。先确认要删除的目标存在。",
                command="ls -la | grep demo",
                explanation="查看是否存在要删除的目标",
                is_complete=False,
                next_step="确认后执行删除"
            )
        elif self.step == 1:
            self.step += 1
            return LLMResponse(
                thinking="找到了目标文件/目录，准备执行删除操作。",
                command="rm -rf demo_folder",
                explanation="删除 demo_folder 目录及其内容",
                is_complete=False,
                next_step="验证删除是否成功",
                is_dangerous=True,
                danger_reason="rm -rf 命令会递归删除目录及其所有内容，此操作不可逆"
            )
        else:
            return LLMResponse(
                thinking="删除操作完成。",
                is_complete=True
            )
    
    def _handle_generic(self) -> LLMResponse:
        """处理通用任务"""
        if self.step == 0:
            self.step += 1
            return LLMResponse(
                thinking="分析任务需求，首先了解当前环境。",
                command="pwd && ls -la",
                explanation="显示当前目录和文件列表",
                is_complete=False,
                next_step="根据环境信息决定下一步"
            )
        else:
            return LLMResponse(
                thinking="演示模式下的通用响应。实际使用时 LLM 会根据任务生成更精确的命令。",
                is_complete=True
            )
