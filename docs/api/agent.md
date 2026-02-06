# Agent

The Agent module implements the core task automation loop.

## Overview

The `AskShell` class orchestrates the entire task execution workflow, managing the interaction between the LLM, command executor, and user interface.

## Class: AskShell

Located in: [`ask_shell/agent.py`](https://github.com/fssqawj/ask-shell/blob/main/ask_shell/agent.py)

### Initialization

```python
from ask_shell.agent import AskShell
from ask_shell.llm import get_llm_client
from ask_shell.executor import ShellExecutor

agent = AskShell(
    llm_client=get_llm_client(),
    executor=ShellExecutor(),
    auto_mode=False
)
```

### Key Methods

#### `execute_task(task: str) -> None`

Execute a single task with the agent loop.

**Parameters:**

- `task` (str): Natural language description of the task

**Example:**

```python
agent.execute_task("list all Python files in current directory")
```

#### `run_interactive() -> None`

Start interactive mode for continuous task execution.

**Example:**

```python
agent.run_interactive()
```

### Agent Loop Pattern

The agent follows this execution loop:

```
1. Receive task
2. Analyze and plan
3. Select appropriate skill (Command, Direct LLM, Browser, PPT, Image, WeChat, Feishu, etc.)
4. Execute skill
5. Safety check (if command-generating skill)
6. Get user confirmation (unless auto mode)
7. Execute command (if applicable)
8. Analyze results
9. Determine if task complete
   - If not complete: goto step 3 with updated context
   - If complete: finish
```

## Architecture

### Component Interaction

```
TaskAgent
  ├─> SkillManager (select and execute appropriate skills)
  │   ├─> CommandSkill (command generation, translation, analysis)
  │   ├─> DirectLLMSkill (direct LLM processing for translation, summaries, etc.)
  │   ├─> BrowserSkill (web automation with Playwright)
  │   ├─> PPTSkill (presentation generation)
  │   ├─> ImageSkill (image generation)
  │   ├─> WeChatSkill (WeChat automation for macOS)
  │   ├─> FeishuSkill (Feishu/Lark automation for macOS)
  │   ├─> Dynamic Skills (auto-generated from markdown with persistent storage)
  │   └─> Other skills...
  ├─> LLMClient (generate commands and analyze)
  ├─> MemoryBank (contextual memory for learning from previous steps)
  ├─> ShellExecutor (execute and validate)
  └─> Console (user interaction and display)
```

### Context Management

The agent maintains conversation context including:

- User's original task
- Commands generated and executed
- Command outputs and results
- Error messages and failures
- Current working directory
- Execution history

### Error Recovery

When command execution fails:

1. **Capture error**: Exit code, stderr, stdout
2. **Analyze failure**: Send error to LLM for analysis
3. **Generate alternative**: LLM suggests different approach
4. **Retry**: Execute alternative command
5. **Repeat**: Up to max retries (default: 3)

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: API key for LLM
- `OPENAI_API_BASE`: Optional custom endpoint
- `MODEL_NAME`: LLM model to use

### Agent Parameters

```python
class AskShell:
    def __init__(
        self,
        auto_execute: bool = False,
        working_dir: Optional[str] = None,
        direct_mode: bool = False
    ):
        ...
```

**Parameters:**

- `llm_client`: Instance of LLM client
- `executor`: Shell command executor
- `auto_mode`: Skip user confirmations if True
- `max_retries`: Maximum retry attempts for failed commands
- `workdir`: Working directory for command execution

## Example Usage

### Basic Task Execution

```python
from ask_shell.agent import AskShell

# Initialize components
agent = AskShell()

# Execute task
agent.run("find all large files")
```

### With Custom Configuration

```python
import os
from ask_shell.agent import AskShell

# Custom configuration
os.environ['MODEL_NAME'] = 'gpt-4'

# Agent with auto mode and custom workdir
agent = AskShell(
    auto_execute=True,
    working_dir='/path/to/project'
)

agent.run("run tests")
```

### Interactive Session

```python
# Start interactive mode
agent = AskShell()
agent.run_interactive()
```

## Extending the Agent

### Custom Agent Subclass

```python
from ask_shell.agent import AskShell

class CustomAgent(AskShell):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Custom initialization
        
    def before_execution(self, command: str):
        """Hook called before command execution"""
        # Log to file
        with open('command_log.txt', 'a') as f:
            f.write(f"{command}\n")
    
    def after_execution(self, result: dict):
        """Hook called after command execution"""
        # Custom result processing
        if result.get('returncode') != 0:
            self.notify_admin(result)
```

### Custom Retry Logic

```python
class SmartAgent(AskShell):
    def should_retry(self, error: str, attempt: int) -> bool:
        """Custom retry decision logic"""
        # Don't retry authentication errors
        if 'permission denied' in error.lower():
            return False
        
        # Retry network errors up to 5 times
        if 'connection refused' in error.lower():
            return attempt < 5
        
        # Default behavior - note: AskShell doesn't have max_retries as a property
        return attempt < 3  # Default max retries
```

## Best Practices

### 1. Context Management

Provide relevant context to improve command generation:

```python
# Context is managed automatically by AskShell
agent.run("commit changes")
```

### 2. Error Handling

Handle agent exceptions gracefully:

```python
try:
    agent.run(user_input)
except Exception as e:
    print(f"Task execution failed: {e}")
    # Handle the error as needed
```

### 3. Resource Cleanup

Ensure proper cleanup in long-running sessions:

```python
try:
    agent.run_interactive()
finally:
    # Resource cleanup happens automatically
    pass
```

## API Reference

### TaskAgent Class

```python
class AskShell:
    """Main task automation agent"""
    
    def run(self, task: str) -> None:
        """Execute a single task"""
        pass
    
    def run_interactive(self) -> None:
        """Start interactive mode"""
        pass
```

## See Also

- [LLM Client API](llm.md)
- [Executor API](executor.md)
- [UI Components](ui.md)
- [Memory System API](memory.md)
- [Skills System API](skills.md)
- [Architecture Overview](../development/architecture.md)
