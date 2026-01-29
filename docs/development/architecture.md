# Architecture

Understanding Ask-Shell's design and architecture.

## High-Level Overview

Ask-Shell follows a modular, layered architecture with a flexible skill system:

```
┌─────────────────────────────────────────────────┐
│              CLI Interface                      │
│           (ask_shell/cli.py)                    │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              Task Agent Layer                   │
│            (ask_shell/agent.py)                 │
│  ┌─────────────────────────────────────────┐    │
│  │  Task Execution Loop                    │    │
│  │  - Analyze task                         │    │
│  │  - Select appropriate skill             │    │
│  │  - Generate commands/responses          │    │
│  │  - Handle errors                        │    │
│  │  - Manage context                       │    │
│  └─────────────────────────────────────────┘    │
└─────────┬─────────────────────┬─────────────────┘
          │                     │
    ┌─────▼─────┐        ┌──────▼─────────────────┐
    │ Skill     │        │  Core Components       │
    │ System    │        │                        │
    │           │        │  ┌───────────────────┐ │
    │  ┌────────▼───┐    │  │  LLM Client       │ │
    │  │ LLMSkill   │    │  │  (llm/*.py)       │ │
    │  │ PPTSkill   │    │  │  - OpenAI API     │ │
    │  │ ImageSkill │────┼─▶│  - Streaming      │ │
    │  │ BrowserSkill│   │  │  - Context mgmt   │ │
    │  │ ...        │    │  └───────────────────┘ │
    │  └────────────┘    │  ┌───────────────────┐ │
    └────────────────────┼─▶│  Shell Executor   │ │
                         │  │ (executor/*.py) │ │
                         │  │  - Command exec   │ │
                         │  │  - Safety check   │ │
                         │  │  - Result parse   │ │
                         │  └───────────────────┘ │
                         │  ┌───────────────────┐ │
                         └─▶│  UI Components    │ │
                            │   (ui/console.py) │ │
                            │  - Rich display   │ │
                            │  - User prompts   │ │
                            │  - Progress anim  │ │
                            └───────────────────┘
```

## Core Components

### 1. CLI Layer

**File**: `ask_shell/cli.py`

**Responsibilities:**

- Parse command-line arguments
- Initialize components
- Coordinate execution modes
- Handle top-level errors

**Key Functions:**

```python
def main():
    """Entry point for ask-shell command"""
    
def parse_arguments():
    """Parse CLI arguments"""
    
def execute_task(args):
    """Execute single task mode"""
    
def interactive_mode(args):
    """Start interactive mode"""
```

### 2. Agent Layer

**File**: `ask_shell/agent.py`

**Responsibilities:**

- Task execution orchestration
- Conversation context management
- Error recovery logic
- Decision making (retry, abort, continue)

**Design Pattern**: Agent Loop

```python
while not task_complete:
    command = llm.generate_command(task, context)
    if executor.is_dangerous(command):
        if not user.confirm():
            continue
    result = executor.execute(command)
    context.add(result)
    task_complete = llm.is_complete(task, context)
```

### 3. LLM Layer

**Files**: `ask_shell/llm/*.py`

**Responsibilities:**

- Communication with AI models
- Prompt engineering
- Response streaming
- Context window management

**Implementations:**

- `openai_client.py`: OpenAI API integration
- `mock.py`: Demo mode simulation
- `base.py`: Abstract interface

**Key Methods:**

```python
class LLMClient:
    def generate_command(self, task, context):
        """Generate shell command for task"""
    
    def analyze_safety(self, command):
        """Analyze command safety"""
    
    def analyze_result(self, command, output):
        """Analyze execution result"""
```

### 4. Executor Layer

**Files**: `ask_shell/executor/*.py`

**Responsibilities:**

- Shell command execution
- Safety validation
- Output capture and parsing
- Environment management

**Safety Mechanisms:**

```python
class ShellExecutor:
    def is_dangerous(self, command):
        """Check if command is dangerous"""
        # 1. Blacklist check
        # 2. AI-powered analysis
        # 3. Scope validation
    
    def execute(self, command, workdir):
        """Execute command safely"""
        # 1. Validate
        # 2. Execute
        # 3. Capture output
        # 4. Parse result
```

### 5. UI Layer

**Files**: `ask_shell/ui/*.py`

**Responsibilities:**

- Terminal output formatting
- User interaction prompts
- Progress indicators
- Syntax highlighting

**Technologies:**

- Rich library for beautiful output
- Markdown rendering
- Live updates and spinners
- Panel-based layouts

## Data Flow

### Task Execution Flow

```
User Input
    │
    ├─> CLI Parser
    │
    └─> TaskAgent.execute_task(task)
            │
            ├─> LLMClient.generate_command(task, context)
            │       │
            │       └─> OpenAI API call
            │               │
            │               └─> Returns command
            │
            ├─> ShellExecutor.is_dangerous(command)
            │       │
            │       ├─> Blacklist check
            │       └─> AI safety analysis
            │
            ├─> Console.confirm(command)
            │       │
            │       └─> User: Y/N/E/Q
            │
            ├─> ShellExecutor.execute(command)
            │       │
            │       └─> subprocess.run(command)
            │               │
            │               └─> Returns result
            │
            ├─> LLMClient.analyze_result(result)
            │       │
            │       └─> Determine next action
            │
            └─> Loop back or Complete
```

### Context Management

```python
class ExecutionContext:
    """Manages conversation context"""
    
    def __init__(self):
        self.messages = []
        self.task = None
        self.results = []
        self.errors = []
    
    def add_command(self, cmd, result):
        """Add command and result to context"""
        self.messages.append({
            "role": "assistant",
            "content": f"Command: {cmd}"
        })
        self.results.append(result)
    
    def get_context_window(self):
        """Get relevant context for next LLM call"""
        # Keep last N messages
        # Summarize old context
        # Maintain task description
```

## Design Patterns

### 1. Strategy Pattern

Different LLM providers implement the same interface:

```python
# Abstract base
class LLMClient(ABC):
    @abstractmethod
    def generate_command(self, task):
        pass

# Concrete implementations
class OpenAIClient(LLMClient):
    def generate_command(self, task):
        # OpenAI implementation
        pass

class MockClient(LLMClient):
    def generate_command(self, task):
        # Simulated responses
        pass
```

### 2. Command Pattern

Shell commands are encapsulated as objects:

```python
class ShellCommand:
    def __init__(self, command, workdir=None):
        self.command = command
        self.workdir = workdir
        self.result = None
    
    def execute(self):
        """Execute the command"""
        pass
    
    def undo(self):
        """Undo if possible"""
        pass
```

### 3. Observer Pattern

UI components observe execution progress:

```python
class ExecutionObserver:
    def on_command_generated(self, command):
        """Called when command is generated"""
        pass
    
    def on_execution_start(self):
        """Called when execution starts"""
        pass
    
    def on_execution_complete(self, result):
        """Called when execution completes"""
        pass
```

## Safety Architecture

### Dual-Layer Protection

```
Command Request
    │
    ├─> Layer 1: Blacklist Check
    │       │
    │       ├─ Match dangerous patterns?
    │       │   Yes -> BLOCK
    │       │   No  -> Continue
    │
    └─> Layer 2: AI Analysis
            │
            ├─ Analyze context and intent
            ├─ Assess risk level
            ├─ Suggest alternatives
            │
            └─> User Confirmation
                    │
                    ├─ Y -> Execute
                    ├─ N -> Skip
                    ├─ E -> Edit
                    └─ Q -> Quit
```

## Scalability Considerations

### Future Enhancements

**1. Plugin System**

```python
class PluginInterface:
    def before_execution(self, command):
        """Hook before command execution"""
    
    def after_execution(self, result):
        """Hook after command execution"""
    
    def custom_command(self, name, args):
        """Handle custom commands"""
```

**2. Distributed Execution**

For running commands on remote servers:

```python
class RemoteExecutor(ShellExecutor):
    def __init__(self, ssh_config):
        self.ssh = SSH(ssh_config)
    
    def execute(self, command):
        return self.ssh.run(command)
```

**3. Task History**

Persistent storage of execution history:

```python
class TaskHistory:
    def save_task(self, task, commands, results):
        """Save task execution to database"""
    
    def replay_task(self, task_id):
        """Replay a previous task"""
```

## Technology Stack

### Core Dependencies

- **Python 3.7+**: Core language
- **openai**: LLM API client
- **rich**: Terminal UI
- **python-dotenv**: Environment configuration

### Development Dependencies

- **pytest**: Testing framework
- **black**: Code formatting
- **mkdocs-material**: Documentation

## Code Organization

```
ask-shell/
├── ask_shell/
│   ├── __init__.py          # Package init
│   ├── cli.py               # CLI entry point
│   ├── agent.py             # Task agent
│   │
│   ├── llm/                 # LLM clients
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract interface
│   │   ├── openai_client.py # OpenAI implementation
│   │   └── mock.py          # Demo mode
│   │
│   ├── executor/            # Command execution
│   │   ├── __init__.py
│   │   └── shell.py         # Shell executor
│   │
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   └── types.py         # Type definitions
│   │
│   └── ui/                  # User interface
│       ├── __init__.py
│       └── console.py       # Rich console UI
│
├── docs/                    # Documentation
├── tests/                   # Test suite
├── pyproject.toml          # Project config
└── setup.py                # Setup script
```

## Next Steps

- [View Agent API documentation](../api/agent.md)
- [Understand LLM integration](../api/llm.md)
- [Learn about contributing](contributing.md)
