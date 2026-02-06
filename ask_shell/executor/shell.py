"""Shell 命令执行器"""

import os
import subprocess
from typing import Optional

from ..models.types import ExecutionResult


class ShellExecutor:
    """Shell 命令执行器"""
    
    # 危险命令黑名单
    DANGEROUS_PATTERNS = [
        "rm -rf /",
        "rm -rf /*",
        "mkfs",
        "dd if=",
        ":(){:|:&};:",
        "> /dev/sda",
        "chmod -R 777 /",
        "chown -R",
    ]
    
    def __init__(self, working_dir: Optional[str] = None, timeout: int = 60):
        self.working_dir = working_dir or os.getcwd()
        self.timeout = timeout
    
    def is_dangerous(self, command: str) -> bool:
        """检查命令是否危险"""
        command_lower = command.lower().strip()
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in command_lower:
                return True
        return False
    
    def execute(self, command: str, timeout: Optional[int] = None) -> ExecutionResult:
        """
        执行 shell 命令
        
        Args:
            command: 要执行的命令
            timeout: 超时时间（秒），默认使用实例配置
            
        Returns:
            ExecutionResult: 执行结果
        """
        timeout = timeout or self.timeout
        
        # 安全检查
        if self.is_dangerous(command):
            return ExecutionResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr="拒绝执行: 检测到潜在危险命令"
            )
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "LANG": "en_US.UTF-8"}
            )
            return ExecutionResult(
                command=command,
                returncode=result.returncode,
                stdout=result.stdout if result.stdout else "成功执行命令",
                stderr=result.stderr
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=f"命令执行超时 (>{timeout}秒)"
            )
        except Exception as e:
            return ExecutionResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=f"执行错误: {str(e)}"
            )
    
    def change_directory(self, path: str) -> bool:
        """更改工作目录"""
        try:
            abs_path = os.path.abspath(os.path.join(self.working_dir, path))
            if os.path.isdir(abs_path):
                self.working_dir = abs_path
                return True
        except Exception:
            pass
        return False
