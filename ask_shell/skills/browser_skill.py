"""Browser automation skill using Playwright with anti-bot detection and dynamic execution"""

from typing import Optional, List, Dict, Any
import time
from .base_skill import BaseSkill, SkillCapability, SkillResponse
from ..llm.openai_client import OpenAIClient
import json
import tempfile
import os


class BrowserSkill(BaseSkill):
    """
    Intelligent browser automation skill with anti-bot detection and dynamic execution
    
    This skill uses Playwright with advanced features:
    - Anti-bot detection (stealth mode, realistic user behavior)
    - Dynamic multi-step execution (observe page state, adjust actions)
    - **Persistent browser session** (keep browser open between steps)
    - Navigate to websites
    - Click elements
    - Fill forms
    - Extract data
    - Take screenshots
    - Handle complex web interactions adaptively
    """
    
    # Class-level browser session management for persistence
    _browser_playwright = None  # Playwright instance
    _browser_context = None     # Browser context
    _browser_page = None        # Current page
    _session_active = False     # Whether session is active
    _browser_process = None     # Browser subprocess
    _ws_endpoint_file = '/tmp/ask_shell_browser_ws.txt'  # WebSocket endpoint for reconnection
    _state_file = '/tmp/ask_shell_browser_state/state.json'  # Shared state file for cross-process coordination
    _lock_file = '/tmp/ask_shell_browser_state/lock'  # Lock file for cross-process synchronization
    
    # Operation history to track all browser operations
    _operation_history = []     # List of all operations performed
    
    SYSTEM_PROMPT = """你是一个专业的浏览器自动化专家，擅长编写智能的、能够适应页面动态变化的自动化代码。

**核心原则：**
1. 每次只生成一个小步骤的代码，而不是一次性完成所有操作
2. 在每个步骤后，你会收到页面状态反馈（截图路径、页面内容等）
3. 根据页面反馈动态调整下一步操作
4. 使用反反爬虫技术避免被识别为机器人
5. **重要：浏览器会话是持久化的，不要关闭浏览器！**

**用户任务流程：**
1. 用户描述任务
2. 你生成第一步代码（如初始化浏览器、访问网站）
3. 代码执行后，你会收到执行结果和页面状态
4. 你分析结果，决定下一步操作
5. 重复步骤3-4直到任务完成

**上下文信息说明：**
- 浏览器操作历史：包含之前所有已完成的浏览器操作，帮助你了解当前任务进展
- 当前页面信息：包含当前页面的URL、标题、HTML结构和可见文本内容，用于生成针对性的操作代码
- 上一步执行结果：包含上一步操作的执行结果和输出信息

**导航操作最佳实践：**
- 使用 `page.go_back(timeout=30000)` 带超时参数，避免在没有历史记录时无限等待
- 使用 `page.go_forward(timeout=30000)` 带超时参数
- 使用 `page.goto(url, timeout=30000)` 带超时参数
- 使用 `page.wait_for_load_state('networkidle', timeout=30000)` 带超时参数

**持久化浏览器会话机制：**
- **真正的持久化**：浏览器在整个任务期间保持打开，不会每步都重启
- 第一次执行时：初始化浏览器（带反检测），保存到类级别变量
- 后续执行时：直接使用已经打开的浏览器，继续在当前页面操作
- 任务完成时：系统自动关闭浏览器
- 异常/退出时：确保浏览器被正确关闭

**代码生成模式：**

**所有步骤都使用统一模板（自动管理浏览器生命周期）：**
```
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_shell.skills.browser_skill import BrowserSkill
import time
import random

# 获取或初始化浏览器实例
skill = BrowserSkill()
page = skill.get_or_create_browser()

# === 执行当前步骤的操作 ===
try:
    time.sleep(random.uniform(0.5, 1))
    
    # 你的操作代码
    # 对于导航操作（如 go_back, goto, go_forward），使用超时控制
    # 例如：page.go_back(timeout=30000) 或 page.goto(url, timeout=30000)
    page.goto('https://example.com')
    page.wait_for_load_state('networkidle', timeout=30000)
    
    # 输出信息
    print(f'当前URL: {page.url}')
    print(f'页面标题: {page.title()}')
    
except Exception as e:
    print(f'操作失败: {e}')
    # 不要关闭浏览器，让系统决定何时关闭

# 不要调用 browser.close() 或 skill.cleanup_browser()
# 浏览器会在任务完成时自动关闭

# 注意：对于导航操作，始终使用超时参数，例如：
# page.go_back(timeout=30000)  # 返回上一页，30秒超时
# page.go_forward(timeout=30000)  # 前进到下一页，30秒超时
```

**最后一步（任务完成）时的模板：**
```
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_shell.skills.browser_skill import BrowserSkill
import time
import random

skill = BrowserSkill()
page = skill.get_or_create_browser()

try:
    # 执行最后的操作
    page.screenshot(path='final_screenshot.png')
    print(f'截图已保存: final_screenshot.png')
    print(f'当前URL: {page.url}')
    print(f'页面标题: {page.title()}')
    
    # 标记任务完成，触发浏览器清理
    skill.cleanup_browser()
    print('✅ 浏览器已关闭')
    
except Exception as e:
    print(f'操作失败: {e}')
    skill.cleanup_browser()  # 异常时也要清理
```

**关键注意事项：**
1. 必须使用 BrowserSkill.get_or_create_browser() 获取浏览器实例
2. 不要手动关闭浏览器，除非任务完成
3. 模拟人类行为（随机延迟、慢速输入）
4. 使用智能定位器（多个选择器、.first、.visible）
5. 包含 try-except 错误处理
6. 输出有用信息（截图路径、URL、标题）
7. 每次只执行 1-2 个关键步骤，不要贪多
8. **重要**：任务完成时调用 skill.cleanup_browser() 关闭浏览器
9. 如果是最后一步，is_complete 设为 true
10. 如果需要继续，is_complete 设为 false，并说明 next_action
11. **重要**：利用上下文中的浏览器操作历史和当前页面信息来生成有针对性的代码
12. **重要**：对导航操作（如 go_back, go_forward, goto）使用超时参数，避免无限等待

**响应格式（必须返回 JSON）：**
{
  "thinking": "分析当前任务，决定第一步操作",
  "code": "Python代码（完整可执行的代码）",
  "explanation": "解释这一步要做什么",
  "is_complete": false,
  "is_dangerous": false,
  "danger_reason": "",
  "next_action": "描述下一步计划（如果is_complete=false）"
}"""

    
    def __init__(self):
        super().__init__()
        self.llm = OpenAIClient()
    
    @classmethod
    def get_or_create_browser(cls):
        """
        获取或创建浏览器实例（通过独立进程+CDP连接实现真正的跨步骤持久化）
        
        Returns:
            Page: Playwright 页面对象（同步API包装）
        """
        import os
        import fcntl
        
        # 确保状态目录存在
        os.makedirs(os.path.dirname(cls._state_file), exist_ok=True)
        
        # 使用文件锁确保并发安全
        lock_fd = None
        try:
            # 获取锁
            lock_fd = os.open(cls._lock_file, os.O_CREAT | os.O_RDWR)
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            
            # 检查并连接到现有浏览器状态
            page = cls._try_connect_to_existing_browser()
            if page:
                return page
            
            # 检查端口占用情况并尝试连接
            page = cls._try_connect_to_port_occupied_browser()
            if page:
                return page
            
            # 启动新浏览器
            return cls._launch_new_browser()
            
        finally:
            # 释放锁
            if lock_fd is not None:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)

    @classmethod
    def _read_browser_state(cls):
        """读取浏览器状态文件并验证进程是否仍在运行"""
        import json
        import os
        
        ws_endpoint = None
        browser_pid = None
        
        # 读取共享状态
        if os.path.exists(cls._state_file):
            try:
                with open(cls._state_file, 'r') as f:
                    state = json.load(f)
                    ws_endpoint = state.get('ws_endpoint')
                    browser_pid = state.get('pid')
                    
                    # 检查浏览器进程是否仍在运行
                    if browser_pid and browser_pid != 9222:  # 9222表示端口占用检查，不是实际进程
                        try:
                            # 检查进程是否存在
                            os.kill(browser_pid, 0)
                        except OSError:
                            # 进程不存在，清除状态文件
                            print("⚠️  检测到浏览器进程已停止，清除状态文件")
                            os.remove(cls._state_file)
                            ws_endpoint = None
                            
            except:
                pass
        
        return ws_endpoint, browser_pid

    @classmethod
    def _setup_browser_context_and_page(cls, browser, reuse_existing=True):
        """设置浏览器上下文和页面"""
        # 获取或创建context
        # 为了确保页面状态持久化，我们总是使用相同标识的context
        # 查找已有的ask-shell专用context，如果没有则创建
        context = None
        for ctx in browser.contexts:
            # 尝试通过特定属性识别我们的context
            try:
                # 通过检查特定标识来识别我们的context
                if hasattr(ctx, '_ask_shell_context') or len(browser.contexts) == 1:
                    context = ctx
                    break
            except:
                continue
                        
        if context is None:
            # 尝试复用现有的context，而不是创建新的
            if browser.contexts and reuse_existing:
                # 如果有现成的context，使用第一个
                context = browser.contexts[0]
                print("🔄 复用现有的浏览器上下文")
            else:
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                # 标记这是ask-shell专用的context
                context._ask_shell_context = True
                # 添加反检测脚本
                init_script = '''
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    window.navigator.chrome = {runtime: {}};
                '''
                context.add_init_script(init_script)
                        
        # 在选定的context中查找页面，优先使用非空白页面
        # 为了确保页面状态持久化，我们优先使用之前保存的页面对象（如果它仍然有效）
        page = None
        
        # 首先检查之前保存的页面是否仍然存在于当前context中
        if cls._browser_page and cls._browser_page in context.pages:
            try:
                # 检查页面是否仍然可用
                current_url = cls._browser_page.url
                if current_url and current_url != 'about:blank' and 'chrome://' not in current_url:
                    page = cls._browser_page
                    print(f"🔄 复用之前的浏览器页面（当前URL: {page.url}）")
                else:
                    # 如果之前的页面是空白的，则寻找其他非空白页面
                    for p in context.pages:
                        try:
                            if p.url and p.url != 'about:blank' and 'chrome://' not in p.url:
                                page = p
                                break
                        except:
                            continue
            except:
                # 如果之前的页面不可用，则寻找其他页面
                for p in context.pages:
                    try:
                        if p.url and p.url != 'about:blank' and 'chrome://' not in p.url:
                            page = p
                            break
                    except:
                        continue
        else:
            # 寻找非空白页面
            for p in context.pages:
                try:
                    if p.url and p.url != 'about:blank' and 'chrome://' not in p.url:
                        page = p
                        break
                except:
                    continue
                        
        # 如果没有找到非空白页面，使用第一个可用页面（避免创建新页面）
        if page is None:
            if context.pages:
                page = context.pages[0]
                print(f"♻️  已连接到运行中的浏览器（当前URL: {page.url}）")
            else:
                page = context.new_page()
                print("♻️  已连接到运行中的浏览器（新页面）")
        else:
            print(f"♻️  已连接到运行中的浏览器（当前URL: {page.url}）")
        
        # 更新类级变量
        # Don't create a new playwright instance if one already exists
        # This prevents the "sync API inside async loop" error
        if not cls._browser_playwright:
            try:
                # Check if we're in an async environment
                import asyncio
                loop = asyncio.get_running_loop()
                # If we're in an async environment, we cannot use sync_playwright at all
                # This is a fundamental limitation of Playwright
                # We'll continue without initializing a new instance
                pass  # Just continue without initializing in async context
            except RuntimeError:
                # No event loop running, safe to use sync API
                from playwright.sync_api import sync_playwright
                cls._browser_playwright = sync_playwright().start()
            except Exception as e:
                # Handle case where sync API is used in async environment
                import warnings
                error_msg = str(e)
                if "It looks like you are using Playwright Sync API inside the asyncio loop" in error_msg:
                    # In async environment, we can't initialize sync playwright
                    # Don't issue warning here since it's expected behavior
                    pass
                else:
                    warnings.warn(f"Could not initialize sync Playwright: {e}. Browser may already be initialized.")
        
        cls._browser_context = context
        cls._browser_page = page
        cls._session_active = True
        
        return page
    
    @classmethod
    def _try_connect_to_existing_browser(cls):
        """尝试连接到现有的浏览器实例"""
        import json
        import os
        from playwright.sync_api import sync_playwright
        
        # 再次检查是否有运行中的浏览器（在获取锁后）
        ws_endpoint, browser_pid = cls._read_browser_state()
        
        # 如果状态文件中有endpoint，尝试连接
        if ws_endpoint:
            try:
                # Only initialize new playwright if one doesn't already exist
                # This prevents issues with sync API in async environments
                if not cls._browser_playwright:
                    try:
                        # Check if we're in an async environment
                        import asyncio
                        loop = asyncio.get_running_loop()
                        # If we're in an async environment, we cannot use sync_playwright at all
                        # This is a fundamental limitation of Playwright
                        raise RuntimeError("Cannot initialize sync Playwright in async environment - event loop is running")
                    except RuntimeError:
                        # No event loop running, safe to use sync API
                        from playwright.sync_api import sync_playwright
                        playwright = sync_playwright().start()
                    except Exception as e:
                        # Handle case where sync API is used in async environment
                        import warnings
                        error_msg = str(e)
                        if "It looks like you are using Playwright Sync API inside the asyncio loop" in error_msg:
                            # In async environment, we can't initialize sync playwright
                            # Don't issue warning here since it's expected behavior
                            pass
                            # In this case, we can't initialize a new playwright instance in the async context
                            # We should either use an existing instance or handle the error appropriately
                            if cls._browser_playwright:
                                playwright = cls._browser_playwright
                            else:
                                # If we don't have an existing instance, we can't proceed
                                # In this case, we need to handle the situation gracefully
                                # For now, we'll re-raise the exception, but ideally this method should be async-compatible
                                raise e
                        else:
                            warnings.warn(f"Could not initialize sync Playwright: {e}. Browser may already be initialized.")
                            from playwright.sync_api import sync_playwright
                            playwright = sync_playwright().start()
                else:
                    playwright = cls._browser_playwright
                
                browser = playwright.chromium.connect_over_cdp(ws_endpoint)
                
                page = cls._setup_browser_context_and_page(browser)
                return page
            except Exception as e:
                print(f"⚠️  连接现有浏览器失败: {e}")
                # 如果连接失败，删除状态文件
                if os.path.exists(cls._state_file):
                    os.remove(cls._state_file)
                print("⚠️  之前的浏览器进程可能已停止，将启动新浏览器")
        
        return None
    
    @classmethod
    def _is_port_in_use(cls, port):
        """检查指定端口是否被占用"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    @classmethod
    def _try_connect_to_port_occupied_browser(cls):
        """尝试连接到端口被占用的浏览器实例"""
        import requests
        import json
        from playwright.sync_api import sync_playwright
        
        if cls._is_port_in_use(9222):
            print("⚠️  端口9222已被占用，可能已有Chrome实例在运行")
            # 尝试连接到可能已存在的浏览器
            try:
                response = requests.get('http://localhost:9222/json/version', timeout=3)
                if response.status_code == 200:
                    ws_endpoint = response.json()['webSocketDebuggerUrl']
                    
                    # 保存到状态文件
                    with open(cls._state_file, 'w') as f:
                        json.dump({'ws_endpoint': ws_endpoint, 'pid': 9222}, f)
                    print("✅ 检测到现有Chrome实例，将复用")
                    
                    # Only initialize new playwright if one doesn't already exist
                    # This prevents issues with sync API in async environments
                    if not cls._browser_playwright:
                        try:
                            # Check if we're in an async environment
                            import asyncio
                            loop = asyncio.get_running_loop()
                            # If we're in an async environment, we cannot use sync_playwright at all
                            # This is a fundamental limitation of Playwright
                            raise RuntimeError("Cannot initialize sync Playwright in async environment - event loop is running")
                        except RuntimeError:
                            # No event loop running, safe to use sync API
                            from playwright.sync_api import sync_playwright
                            playwright = sync_playwright().start()
                        except Exception as e:
                            # Handle case where sync API is used in async environment
                            import warnings
                            error_msg = str(e)
                            if "It looks like you are using Playwright Sync API inside the asyncio loop" in error_msg:
                                # In async environment, we can't initialize sync playwright
                                # Don't issue warning here since it's expected behavior
                                pass
                                # In this case, we can't initialize a new playwright instance in the async context
                                # We should either use an existing instance or handle the error appropriately
                                if cls._browser_playwright:
                                    playwright = cls._browser_playwright
                                else:
                                    # If we don't have an existing instance, we can't proceed
                                    # In this case, we need to handle the situation gracefully
                                    # For now, we'll re-raise the exception, but ideally this method should be async-compatible
                                    raise e
                            else:
                                warnings.warn(f"Could not initialize sync Playwright: {e}. Browser may already be initialized.")
                                from playwright.sync_api import sync_playwright
                                playwright = sync_playwright().start()
                    else:
                        playwright = cls._browser_playwright
                    
                    browser = playwright.chromium.connect_over_cdp(ws_endpoint)
                    
                    page = cls._setup_browser_context_and_page(browser)
                    return page
            except Exception as e:
                print(f"⚠️  连接现有实例失败: {e}，将启动新浏览器")
        
        return None
    
    @classmethod
    def _launch_new_browser(cls):
        """启动一个新的浏览器实例"""
        import os
        import subprocess
        import time
        import requests
        from playwright.sync_api import sync_playwright
        
        # 如果没有现有浏览器，启动独立的Chrome进程（使用CDP）
        print("🚀 正在启动独立的浏览器进程...")
        
        # 使用Chrome的远程调试端口
        chrome_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
        ]
        
        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                break
        
        if not chrome_path:
            # 回退到Playwright的browser
            print("⚠️  未找到Chrome，使用Playwright的Chromium")
            # Only initialize new playwright if one doesn't already exist
            # This prevents issues with sync API in async environments
            if not cls._browser_playwright:
                try:
                    from playwright.sync_api import sync_playwright
                    playwright = sync_playwright().start()
                except Exception as e:
                    # Handle case where sync API is used in async environment
                    import warnings
                    error_msg = str(e)
                    if "It looks like you are using Playwright Sync API inside the asyncio loop" in error_msg:
                        warnings.warn(f"Sync Playwright API cannot be used inside async loop: {e}. Browser may already be initialized.")
                        # In async environment, we can't initialize sync playwright
                        if cls._browser_playwright:
                            playwright = cls._browser_playwright
                        else:
                            # If no existing instance, we can't proceed in async context
                            raise e
                    else:
                        warnings.warn(f"Could not initialize sync Playwright: {e}. Browser may already be initialized.")
                        from playwright.sync_api import sync_playwright
                        playwright = sync_playwright().start()
            else:
                playwright = cls._browser_playwright
            
            browser = playwright.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            init_script = '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.navigator.chrome = {runtime: {}};
            '''
            context.add_init_script(init_script)
            page = context.new_page()
            
            # 更新类级变量
            cls._browser_playwright = playwright
            cls._browser_context = context
            cls._browser_page = page
            cls._session_active = True
            
            print("✨ 浏览器已启动（注意：进程结束后会关闭）")
            return page
        
        # 启动独立的Chrome进程（只有在没有检测到现有实例时）
        user_data_dir = '/tmp/ask_shell_chrome_profile'
        os.makedirs(user_data_dir, exist_ok=True)
        
        cls._browser_process = subprocess.Popen([
            chrome_path,
            f'--user-data-dir={user_data_dir}',
            '--remote-debugging-port=9222',
            '--disable-blink-features=AutomationControlled',
            '--no-first-run',
            '--no-default-browser-check',
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 等待浏览器启动（更长时间）
        print("⏳ 等待浏览器启动...")
        max_retries = 15
        for i in range(max_retries):
            time.sleep(1)
            try:
                response = requests.get('http://localhost:9222/json/version', timeout=2)
                if response.status_code == 200:
                    print("✅ 浏览器已就绪")
                    break
            except:
                if i == max_retries - 1:
                    raise
                continue
        
        # 获取WebSocket endpoint
        try:
            response = requests.get('http://localhost:9222/json/version', timeout=5)
            ws_endpoint = response.json()['webSocketDebuggerUrl']
            
            # 保存到状态文件
            with open(cls._state_file, 'w') as f:
                json.dump({'ws_endpoint': ws_endpoint, 'pid': cls._browser_process.pid}, f)
            
            # 初始化 Playwright
            # Check if we're in an async environment to avoid Playwright sync API errors
            import asyncio
            playwright = None
            try:
                # Check if we're in an async environment
                loop = asyncio.get_running_loop()
                # If we're in an async environment, we cannot use sync_playwright at all
                # This is a fundamental limitation of Playwright
                raise RuntimeError("Cannot initialize sync Playwright in async environment - event loop is running")
            except RuntimeError:
                # No event loop running, safe to use sync API
                from playwright.sync_api import sync_playwright
                playwright = sync_playwright().start()
            except Exception as e:
                # Handle case where sync API is used in async environment
                import warnings
                error_msg = str(e)
                if "It looks like you are using Playwright Sync API inside the asyncio loop" in error_msg:
                    # In async environment, we can't initialize sync playwright
                    # Don't issue warning here since it's expected behavior
                    pass
                    # In this case, we can't initialize a new playwright instance in the async context
                    # We should either use an existing instance or handle the error appropriately
                    if cls._browser_playwright:
                        playwright = cls._browser_playwright
                    else:
                        # If we don't have an existing instance, we can't proceed
                        # In this case, we need to handle the situation gracefully
                        # For now, we'll re-raise the exception, but ideally this method should be async-compatible
                        raise e
                else:
                    # Some other error, re-raise
                    raise e
            
            # 连接到浏览器
            browser = playwright.chromium.connect_over_cdp(ws_endpoint)
            
            # 尝试复用现有的context，而不是创建新的
            if browser.contexts:
                # 如果有现成的context，使用第一个
                context = browser.contexts[0]
                print("🔄 复用现有的浏览器上下文")
            else:
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                
                # 添加反检测脚本
                init_script = '''
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    window.navigator.chrome = {runtime: {}};
                '''
                context.add_init_script(init_script)
            
            # 尝试复用现有的页面，而不是创建新的
            if context.pages:
                page = context.pages[0]
                print(f"🔄 复用现有的浏览器页面（当前URL: {page.url}）")
            else:
                # 创建页面
                page = context.new_page()
            
            # 更新类级变量
            cls._browser_playwright = playwright
            cls._browser_context = context
            cls._browser_page = page
            cls._session_active = True
                    
            print(f"✨ 独立浏览器进程已启动（PID: {cls._browser_process.pid}），会话将保持打开")
                    
            return page
            
        except Exception as e:
            print(f"❌ 启动浏览器失败: {e}")
            if cls._browser_process:
                cls._browser_process.terminate()
            raise
    
    @classmethod
    def cleanup_browser(cls):
        """
        清理浏览器资源
        """
        import os
        import shutil
        import signal
        from playwright.sync_api import sync_playwright
        
        # 仅在有需要清理的组件时显示开始清理信息
        has_components = cls._browser_context is not None or cls._browser_playwright is not None or cls._browser_process is not None
        if has_components:
            print("🔄 开始清理浏览器资源...")
        try:
            # 关闭 Playwright 连接
            if cls._browser_context:
                try:
                    cls._browser_context.close()
                    print("✅ 已关闭浏览器上下文")
                except Exception as e:
                    print(f"⚠️  关闭浏览器上下文失败: {e}")
            # 无需显示上下文未找到的消息，这很常见

            if cls._browser_playwright:
                try:
                    cls._browser_playwright.stop()
                    print("✅ 已停止 Playwright")
                except Exception as e:
                    print(f"⚠️  停止 Playwright 失败: {e}")
            # 无需显示Playwright实例未找到的消息，这很常见

            # 杀掉独立的浏览器进程
            if cls._browser_process and cls._browser_process.poll() is None:
                print(f"🚧 正在关闭浏览器进程 (PID: {cls._browser_process.pid})")
                cls._browser_process.terminate()
                try:
                    cls._browser_process.wait(timeout=5)
                    print("✅ 浏览器进程已终止")
                except Exception as wait_e:
                    print(f"⚠️  等待浏览器进程终止超时: {wait_e}")
                    cls._browser_process.kill()
                    print("✅ 浏览器进程已强制终止")
            # 无需显示浏览器进程状态消息，这很常见

            # 尝试通过 WebSocket 连接关闭浏览器（如果状态文件存在）
            try:
                if os.path.exists(cls._state_file):
                    with open(cls._state_file, 'r') as f:
                        state = json.load(f)
                        ws_endpoint = state.get('ws_endpoint')
                        if ws_endpoint:
                            import requests
                            try:
                                # 尝试发送关闭命令到浏览器
                                shutdown_url = ws_endpoint.replace('devtools/browser', 'json/close')
                                # 或者使用 /json/activate 端点
                                resp = requests.post(f'{shutdown_url.rsplit("/", 1)[0]}/close')
                            except:
                                pass  # 忽略WebSocket关闭失败
                                # 尝试另一种方式关闭
                                try:
                                    browser_url = ws_endpoint.replace('ws://', 'http://').replace('/devtools/browser', '/json')
                                    resp = requests.get(browser_url)
                                    tabs = resp.json()
                                    for tab in tabs:
                                        if 'webSocketDebuggerUrl' in tab:
                                            close_url = tab['url'].replace('ws://', 'http://').replace('/devtools/browser', f"/json/close/{tab['id']}")
                                            try:
                                                requests.get(close_url)
                                            except:
                                                pass  # 忽略错误
                                except:
                                    pass  # 忽略错误
            except:
                pass  # 忽略整个WebSocket关闭过程的错误

            # 尝试使用pkill命令终止Chrome进程
            try:
                import subprocess
                result = subprocess.run(['pgrep', '-f', 'Google Chrome.*remote-debugging-port=9222'], 
                                  capture_output=True, text=True)
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid:
                            subprocess.run(['kill', '-9', pid])
            except:
                pass  # 忽略pkill失败

            # 重置状态
            cls._browser_playwright = None
            cls._browser_context = None
            cls._browser_page = None
            cls._browser_process = None
            cls._session_active = False

            # 删除endpoint文件
            if os.path.exists(cls._ws_endpoint_file):
                try:
                    os.remove(cls._ws_endpoint_file)
                except:
                    pass  # 忽略删除endpoint文件失败

            # 删除状态文件
            if os.path.exists(cls._state_file):
                try:
                    os.remove(cls._state_file)
                except:
                    pass  # 忽略删除状态文件失败

            # 清理用户数据目录（可选）
            user_data_dir = '/tmp/ask_shell_chrome_profile'
            if os.path.exists(user_data_dir):
                try:
                    shutil.rmtree(user_data_dir, ignore_errors=True)
                except:
                    pass  # 忽略清理用户数据目录失败

            print("✅ 浏览器资源已完全清理")
        except Exception as e:
            print(f"⚠️  浏览器清理失败: {e}")
            import traceback
            traceback.print_exc()
    
    @classmethod
    def add_operation_to_history(cls, operation_desc: str):
        """Add an operation to the history"""
        cls._operation_history.append({
            'step': len(cls._operation_history) + 1,
            'timestamp': time.time(),
            'operation': operation_desc
        })
        
        # Keep only the last 20 operations to prevent unlimited growth
        if len(cls._operation_history) > 20:
            cls._operation_history = cls._operation_history[-20:]
    
    @classmethod
    def get_operation_history(cls) -> List[Dict[str, Any]]:
        """Get the operation history"""
        return cls._operation_history
    
    @classmethod
    def clear_operation_history(cls):
        """Clear the operation history"""
        cls._operation_history = []
    
    @classmethod
    def get_current_page_structure(cls) -> str:
        """Get the current page structure (HTML content and elements)"""
        if cls._browser_page:
            try:
                # Get page title
                title = cls._browser_page.title()
                
                # Get URL
                url = cls._browser_page.url
                
                # Get page content (HTML)
                html_content = cls._browser_page.content()
                
                # Get visible text content
                body_text = cls._browser_page.text_content('body')
                
                # Limit content size to avoid overwhelming the LLM
                max_content_size = 2000
                if len(html_content) > max_content_size:
                    html_content = html_content[:max_content_size] + "...(truncated)"
                
                if len(body_text) > max_content_size:
                    body_text = body_text[:max_content_size] + "...(truncated)"
                
                structure_info = f"""=== 当前页面信息 ===
URL: {url}
标题: {title}

页面结构 (HTML片段):
{html_content}

页面可见文本 (部分):
{body_text}"""
                
                return structure_info
            except Exception as e:
                return f"获取页面结构失败: {str(e)}"
        else:
            return "浏览器页面未初始化，无法获取页面结构"
    
    def reset(self):
        """重置技能状态（会被 agent 调用）"""
        # 关闭浏览器
        self.cleanup_browser()
        # Clear operation history
        self.clear_operation_history()
    
    def get_capabilities(self) -> List[SkillCapability]:
        """Return browser automation capability"""
        return [SkillCapability.WEB_INTERACTION]
    
    def get_description(self) -> str:
        """Get description of this skill"""
        return (
            "BrowserSkill: 使用 Playwright 自动化 Chrome 浏览器操作，"
            "包括网页导航、元素点击、表单填写、数据提取和截图等功能"
        )
    
    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream_callback=None,
        **kwargs
    ) -> SkillResponse:
        """
        Execute browser automation task
        
        Args:
            task: User's browser automation request
            context: Execution context (history, last result, etc.)
            stream_callback: Callback for streaming output
            **kwargs: Additional parameters
            
        Returns:
            SkillResponse with generated Playwright code
        """
        # Build context information
        context_info = self._build_context_info(context)
        
        # Build user message
        user_message = f"""用户任务：{task}

{context_info}

请生成 Playwright 代码来完成这个浏览器操作任务。"""
        
        # Call LLM to generate browser automation code
        try:
            response_text = self.llm.chat(
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                stream_callback=stream_callback
            )
            
            # Debug: print response if empty
            if not response_text or not response_text.strip():
                return SkillResponse(
                    skill_name=self.name,
                    thinking="LLM返回了空响应",
                    direct_response="错误：LLM未能生成浏览器自动化代码",
                    is_complete=True
                )
            
            # Parse LLM response
            response_data = self._parse_llm_response(response_text)
            
            # print(f"[DEBUG] Parsed Response Data: {response_data}")  # 仅在调试时启用
            
            # Check if code was generated
            code = response_data.get("code", "").strip()
            if not code:
                # print(f"[DEBUG] No code generated! Response data: {response_data}")  # 仅在调试时启用
                return SkillResponse(
                    skill_name=self.name,
                    thinking=response_data.get("thinking", "未生成代码"),
                    direct_response=f"错误：未能生成可执行代码。LLM响应: {response_data.get('explanation', '无说明')}",
                    is_complete=True
                )
            
            # Record the operation in history
            explanation = response_data.get("explanation", "未知操作")
            # Include a summary of the code being executed
            code_summary = code[:100].replace('\n', ' ') + ('...' if len(code) > 100 else '')
            operation_desc = f"{explanation} - 代码: {code_summary}"
            self.add_operation_to_history(operation_desc)
            
            # Generate command to execute the code
            command = self._generate_execution_command(code)
            
            # 是否需要LLM处理由skill selector根据任务执行状态智能判断，不需要在这里进行关键词匹配
            needs_llm_processing = False
            
            # 修改生成的代码，将截图和其他文件保存到 /tmp 目录
            import re
            # 移除截图操作，保留其他功能
            import re
            # 移除所有截图相关的代码行
            lines = code.split('\n')
            filtered_lines = []
            for line in lines:
                # 跳过包含截图操作的行
                if 'screenshot' not in line.lower() and '.png' not in line.lower():
                    filtered_lines.append(line)
            code = '\n'.join(filtered_lines)
            
            # 替换文件打开操作
            def replace_open(match):
                filename = match.group(1)
                return f"open('/tmp/{filename}',"
            code = re.sub(r"open\s*\(\s*['\"]([a-zA-Z0-9_\-\.]+\.[a-zA-Z]{3,4})['\"],", replace_open, code)
            
            # 替换其他可能的文件名
            def replace_filename(match):
                filename = match.group(1)
                return f"'/tmp/{filename}'"
            code = re.sub(r"['\"]([a-zA-Z0-9_\-\.]+\.txt)['\"]", replace_filename, code)
            
            # 重新生成执行命令
            command = self._generate_execution_command(code)
            
            # Check if this is the final step and if we should clean up the browser
            is_complete = response_data.get("is_complete", True)
            
            # Create the response
            response = SkillResponse(
                skill_name=self.name,
                thinking=response_data.get("thinking", ""),
                command=command,
                explanation=response_data.get("explanation", ""),
                is_dangerous=response_data.get("is_dangerous", False),
                danger_reason=response_data.get("danger_reason", ""),
                is_complete=is_complete,
                needs_llm_processing=needs_llm_processing
            )
            
            # If this is the final step, schedule browser cleanup
            if is_complete:
                # Note: We can't call cleanup_browser() directly here because the command
                # will be executed separately. The actual cleanup needs to happen elsewhere.
                # The agent should handle cleanup when the skill chain completes.
                pass

            return response
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return SkillResponse(
                skill_name=self.name,
                thinking=f"生成浏览器自动化代码失败: {str(e)}",
                direct_response=f"错误: {str(e)}\n\n详细信息：\n{error_details}",
                is_complete=True
            )
    
    def _build_context_info(self, context: Optional[Dict[str, Any]]) -> str:
        """Build context information string with page state feedback"""
        if not context:
            return ""
        
        info_parts = []
        
        # Add iteration info
        iteration = context.get("iteration", 1)
        if iteration > 1:
            info_parts.append(f"\n===== 第 {iteration} 次迭代 =====")
        
        # Add operation history
        operation_history = self.get_operation_history()
        if operation_history:
            info_parts.append("\n=== 浏览器操作历史 ===")
            for op in operation_history:
                info_parts.append(f"步骤 {op['step']}: {op['operation']}")
        
        # Add current page structure
        page_structure = self.get_current_page_structure()
        if page_structure:
            info_parts.append(f"\n{page_structure}")
        
        # Add last result if available
        if context.get("last_result"):
            result = context["last_result"]
            info_parts.append(f"\n上一步执行结果：")
            
            if result.returncode == 0:
                info_parts.append("✅ 执行成功")
            else:
                info_parts.append(f"❌ 执行失败（返回码: {result.returncode}）")
            
            # Extract useful information from output
            if result.stdout:
                output = result.stdout.strip()
                
                # Look for screenshot paths
                import re
                screenshot_match = re.search(r'截图已保存: ([^\n]+)', output)
                if screenshot_match:
                    info_parts.append(f"📸 截图: {screenshot_match.group(1)}")
                
                # Look for URLs
                url_match = re.search(r'当前URL: ([^\n]+)', output)
                if url_match:
                    info_parts.append(f"🌐 当前URL: {url_match.group(1)}")
                
                # Look for page titles
                title_match = re.search(r'页面标题: ([^\n]+)', output)
                if title_match:
                    info_parts.append(f"📝 页面标题: {title_match.group(1)}")
                
                # Show first 500 chars of output
                info_parts.append(f"\n输出信息:\n{output[:500]}")
                if len(output) > 500:
                    info_parts.append("...(truncated)")
            
            if result.stderr:
                error_msg = result.stderr.strip()[:300]
                info_parts.append(f"\n错误信息:\n{error_msg}")
        
        return "\n".join(info_parts) if info_parts else ""
    
    def _parse_llm_response(self, response_text: str) -> dict:
        """Parse LLM response to extract structured data"""
        import re
        
        try:
            # Try to parse as JSON
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            # Try to parse JSON
            data = json.loads(text)
            
            # Validate required fields
            if 'code' not in data:
                raise ValueError("Missing 'code' field in response")
            
            return data
            
        except (json.JSONDecodeError, ValueError) as e:
            # If not valid JSON, try to extract code from markdown
            code_match = re.search(r'``python\s*\n(.*?)\n```', response_text, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
                return {
                    "thinking": "从响应中提取了代码",
                    "code": code,
                    "explanation": "使用 Playwright 执行浏览器操作",
                    "is_complete": True,
                    "is_dangerous": False
                }
            
            # Last resort: return error
            return {
                "thinking": f"无法解析LLM响应: {str(e)}",
                "code": "",
                "explanation": f"解析错误，原始响应: {response_text[:200]}",
                "is_complete": True,
                "is_dangerous": False
            }
    
    def _generate_execution_command(self, code: str) -> str:
        """
        Generate command to execute the Playwright code
        
        This saves the code to a temporary file and returns a command to execute it
        """
        import tempfile
        import os
        
        # Create a temporary Python file with the code
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            dir='/tmp'
        ) as f:
            # Modify the code to prevent accidental cleanup in non-final steps
            # Only protect cleanup calls if this is not the final step
            import re
            protected_code = code
            
            # In general, protect cleanup calls in intermediate steps
            protected_code = re.sub(r'skill\.cleanup_browser\(\)', '# PROTECTED: skill.cleanup_browser()', protected_code)
            protected_code = re.sub(r'browser\.close\(\)', '# PROTECTED: browser.close()', protected_code)
            protected_code = re.sub(r'playwright\.stop\(\)', '# PROTECTED: playwright.stop()', protected_code)
            # Also catch variations with assignment or other context
            protected_code = re.sub(r'([^#].*)skill\.cleanup_browser\(\)', r'\1# PROTECTED: skill.cleanup_browser()', protected_code)
            
            # Wrap the code in a function to avoid asyncio issues
            wrapped_code = f'''#!/usr/bin/env python3
import sys
import os
# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Set environment to avoid asyncio issues with Playwright
os.environ['PLAYWRIGHT_FORCE_SYNC'] = '1'

# Ensure clean process context
import asyncio
try:
    # If an event loop is already running, we're in an async context
    loop = asyncio.get_running_loop()
    # In this case, we shouldn't create a new one
except RuntimeError:
    # No event loop running, which is what we want for sync playwright
    pass

def run_browser_task():
{chr(10).join("    " + line for line in protected_code.split(chr(10)))}

if __name__ == "__main__":    
    run_browser_task()
'''
            
            f.write(wrapped_code)
            temp_file = f.name
        
        # Make it executable
        os.chmod(temp_file, 0o755)
        
        # Return command to execute the file
        return f"python3 {temp_file}"
