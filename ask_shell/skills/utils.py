from typing import List, Optional

from ask_shell.memory.bank import MemoryBank
from ..models.types import ExecutionResult


def build_task_message(task: str) -> str:
    """构建任务消息"""
    return f"请帮我完成以下任务: {task}"


def build_full_history_message(history: List[ExecutionResult], task: str = "", memory_bank: Optional[MemoryBank] = None) -> str:
        """
        构建完整的执行历史消息
        
        Args:
            history: 历史执行结果列表
            user_input: 用户输入的任务描述
            last_result: 最后一次执行结果（与history[-1]通常是相同的，但为了兼容性传入）
        """
        if len(history) == 0 and not task:
            return "- 历史执行记录: 无\n"
        if len(history) == 0:
            return build_task_message(task)

        history_str = "历史任务执行摘要:\n"
        # 添加内存银行信息 if available
        if memory_bank:
            # Include summaries
            summaries = memory_bank.get_summaries()
            if summaries:
                history_str += "- 记忆摘要:\n"
                for summary in summaries[-2:]:  # Show last 2 summaries
                    history_str += f"  摘要: {summary.title} - {summary.content}\n"

        history_str += "最近任务执行历史:\n"
        
        for i, result in enumerate(history[-3:]):
            idx = max(len(history) - 2, 1) + i
            status = "成功" if result.success else "失败"
            
            # 智能判断是否需要更多内容：基于输出长度和内容类型
            # 如果输出较短或包含结构化数据，使用完整内容；否则截断
            output = result.get_output_for_llm()  # 默认使用完整内容以提供更多信息
            
            history_str += f"\n第{idx}步 - 命令执行{status}：\n"
            history_str += f"技能选择: {result.skill_response.skill_name}\n"
            history_str += f"技能选择原因: {result.skill_response.select_reason}\n"
            if result.skill_response.thinking:
                history_str += f"技能执行思考过程: {result.skill_response.thinking}\n"
            if result.skill_response.next_step:
                history_str += f"下一步计划: {result.skill_response.next_step}\n"
            if result.command:   
                history_str += f"执行命令: {result.command}\n"
                history_str += f"返回码: {result.returncode}\n"
                history_str += f"命令输出:\n{output}\n"
            if result.skill_response.direct_response:
                history_str += f"直接响应: {result.skill_response.direct_response}\n"
        if task:
            task_current = f"\n\n用户当前的任务是：{task}"
            return f"{history_str}{task_current}"
        return history_str
