#!/usr/bin/env python3
"""Ask-Shell 主程序入口"""

import argparse
import sys
from dotenv import load_dotenv
from loguru import logger
from ask_shell import AskShell


def main():
    """主函数"""
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Ask-Shell - 用自然语言操控你的终端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "列出当前目录下的所有 Python 文件"
  %(prog)s -i                    # 交互模式
  %(prog)s -a "统计代码行数"       # 自动执行模式
  %(prog)s -l "翻译这段文字为英文"  # 直接LLM模式
  %(prog)s --web                  # 启动Web界面
        """
    )
    
    parser.add_argument(
        "task",
        nargs="?",
        help="要执行的任务描述"
    )
    parser.add_argument(
        "--auto", "-a",
        action="store_true",
        help="自动执行模式（不需要确认每条命令）"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="交互模式"
    )
    parser.add_argument(
        "--workdir", "-w",
        type=str,
        default=None,
        help="工作目录"
    )
    parser.add_argument(
        "--llm", "-l",
        action="store_true",
        help="直接LLM模式（用于翻译、总结、分析等任务，不执行命令）"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="启动Web界面"
    )
    parser.add_argument(
        "--no-persistence",
        action="store_true",
        help="禁用技能持久化（不保存生成的技能到文件）"
    )
    
    args = parser.parse_args()
    
    # 启动Web服务器
    if args.web:
        try:
            from ask_shell.web.server import run_web_server
            run_web_server(host='localhost', port=5000, debug=False)
        except ImportError as e:
            print(f"错误: 无法启动Web服务器 - {e}")
            print("提示: 请确保已安装flask和flask-socketio")
            sys.exit(1)
    else:
        # 创建 Agent
        try:
            agent = AskShell(
                auto_execute=args.auto,
                working_dir=args.workdir,
                direct_mode=args.llm,
                enable_persistence=not args.no_persistence
            )
        except Exception as e:
            logger.opt(exception=e).error("初始化失败")
            sys.exit(1)
        
        # 运行
        if args.interactive or not args.task:
            agent.run_interactive()
        else:
            context = agent.run(args.task)
            # 返回非零退出码如果任务失败
            if context.status.value == "failed":
                sys.exit(1)


if __name__ == "__main__":
    main()
