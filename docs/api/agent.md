# Agent

The Agent module implements the core task automation loop.

## Overview

The `Agent` class orchestrates the entire task execution workflow, managing the interaction between the LLM, command executor, and user interface.

## Class: TaskAgent

Located in: [`ask_shell/agent.py`](https://github.com/fssqawj/ask-shell/blob/main/ask_shell/agent.py)

### Initialization

```python
from ask_shell.agent import TaskAgent
from ask_shell.llm import get_llm_client
from ask_shell.executor import ShellExecutor

agent = TaskAgent(
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
3. Select appropriate skill (LLM, Browser, PPT, Image, etc.)
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
  │   ├─> LLMSkill (command generation, translation, analysis)
  │   ├─> BrowserSkill (web automation with Playwright)
  │   ├─> PPTSkill (presentation generation)
  │   ├─> ImageSkill (image generation)
  │   └─> Other skills...
  ├─> LLMClient (generate commands and analyze)
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
class TaskAgent:
    def __init__(
        self,
        llm_client: LLMClient,
        executor: ShellExecutor,
        auto_mode: bool = False,
        max_retries: int = 3,
        workdir: Optional[str] = None
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
from ask_shell.agent import TaskAgent
from ask_shell.llm import get_llm_client
from ask_shell.executor import ShellExecutor

# Initialize components
llm = get_llm_client()
executor = ShellExecutor()
agent = TaskAgent(llm, executor)

# Execute task
agent.execute_task("find all large files")
```

### With Custom Configuration

```python
import os
from ask_shell.agent import TaskAgent
from ask_shell.llm import get_llm_client
from ask_shell.executor import ShellExecutor

# Custom configuration
os.environ['MODEL_NAME'] = 'gpt-4'

llm = get_llm_client()
executor = ShellExecutor()

# Agent with auto mode and custom workdir
agent = TaskAgent(
    llm_client=llm,
    executor=executor,
    auto_mode=True,
    max_retries=5,
    workdir='/path/to/project'
)

agent.execute_task("run tests")
```

### Interactive Session

```python
# Start interactive mode
agent = TaskAgent(llm, executor)
agent.run_interactive()
```

## Extending the Agent

### Custom Agent Subclass

```python
from ask_shell.agent import TaskAgent

class CustomAgent(TaskAgent):
    def before_execution(self, command: str):
        """Hook called before command execution"""
        # Log to file
        with open('command_log.txt', 'a') as f:
            f.write(f"{command}\n")
    
    def after_execution(self, result: dict):
        """Hook called after command execution"""
        # Custom result processing
        if result.get('exit_code') != 0:
            self.notify_admin(result)
```

### Custom Retry Logic

```python
class SmartAgent(TaskAgent):
    def should_retry(self, error: str, attempt: int) -> bool:
        """Custom retry decision logic"""
        # Don't retry authentication errors
        if 'permission denied' in error.lower():
            return False
        
        # Retry network errors up to 5 times
        if 'connection refused' in error.lower():
            return attempt < 5
        
        # Default behavior
        return attempt < self.max_retries
```

## Best Practices

### 1. Context Management

Provide relevant context to improve command generation:

```python
# Include git status in context
result = executor.execute("git status")
agent.add_context("Git status", result)

agent.execute_task("commit changes")
```

### 2. Error Handling

Handle agent exceptions gracefully:

```python
from ask_shell.exceptions import ExecutionError, LLMError

try:
    agent.execute_task(user_input)
except LLMError as e:
    print(f"AI service error: {e}")
    # Fallback to demo mode or retry
except ExecutionError as e:
    print(f"Execution failed: {e}")
    # Log and continue
```

### 3. Resource Cleanup

Ensure proper cleanup in long-running sessions:

```python
try:
    agent.run_interactive()
finally:
    agent.cleanup()  # Close connections, save state, etc.
```

## API Reference

### TaskAgent Class

```python
class TaskAgent:
    """Main task automation agent"""
    
    def execute_task(self, task: str) -> None:
        """Execute a single task"""
        pass
    
    def run_interactive(self) -> None:
        """Start interactive mode"""
        pass
    
    def add_context(self, key: str, value: Any) -> None:
        """Add context information"""
        pass
    
    def clear_context(self) -> None:
        """Clear conversation context"""
        pass
```

## See Also

- [LLM Client API](llm.md)
- [Executor API](executor.md)
- [UI Components](ui.md)
- [Architecture Overview](../development/architecture.md)
