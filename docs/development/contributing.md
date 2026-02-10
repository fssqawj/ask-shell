# Contributing to Ask-Shell

Thank you for your interest in contributing to Ask-Shell! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## Ways to Contribute

### 1. Report Bugs

Found a bug? Please create an issue with:

- **Description**: What happened vs. what you expected
- **Steps to reproduce**: Minimal example to reproduce the issue
- **Environment**: OS, Python version, Ask-Shell version
- **Logs**: Error messages or relevant output

**Example:**

```markdown
## Bug Description
Ask-Shell crashes when trying to execute git commands

## Steps to Reproduce
1. Run: `ask "check git status"`
2. Error occurs immediately

## Environment
- OS: macOS 13.0
- Python: 3.9.5
- Ask-Shell: 0.1.0

## Error Log
```
Traceback (most recent call last):
  ...
```

### 2. Suggest Features

Have an idea? Open an issue with:

- **Use case**: Why is this feature needed?
- **Proposed solution**: How should it work?
- **Alternatives**: Other approaches considered

### 3. Improve Documentation

Documentation improvements are always welcome:

- Fix typos or unclear explanations
- Add examples
- Improve code comments
- Create tutorials

### 4. Submit Code

Ready to code? Great! Follow the development workflow below.

## Development Workflow

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR-USERNAME/alpha-bot.git
cd alpha-bot

# Add upstream remote
git remote add upstream https://github.com/fssqawj/alpha-bot.git
```

### 2. Create a Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

Branch naming conventions:

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring

### 3. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

### 4. Make Changes

Follow our coding standards:

**Code Style:**

- Use [Black](https://github.com/psf/black) for formatting
- Follow PEP 8 guidelines
- Maximum line length: 88 characters (Black default)

**Format your code:**

```bash
black ask_shell/
```

**Type hints:**

```python
def execute_task(self, task: str) -> None:
    """Execute a task with type hints"""
    pass
```

**Docstrings:**

```python
def generate_command(self, task: str, context: dict) -> str:
    """Generate shell command from task description.
    
    Args:
        task: Natural language task description
        context: Execution context with history
    
    Returns:
        Shell command string
    
    Raises:
        LLMError: If API call fails
    """
    pass
```

### 5. Add Tests

All new features should include tests:

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=ask_shell

# Run specific test
pytest tests/test_agent.py::test_execute_task
```

**Example test:**

```python
def test_agent_executes_simple_task():
    """Test agent can execute a simple task"""
    agent = TaskAgent(MockLLM(), ShellExecutor())
    
    # Should not raise
    agent.execute_task("list files")
    
    # Verify command was executed
    assert len(agent.executed_commands) == 1
```

### 6. Commit Changes

**Commit message format:**

```
<type>: <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example:**

```bash
git commit -m "feat: add support for custom LLM providers

Implemented plugin interface for LLM providers
allowing users to integrate custom AI models.

- Added LLMProvider abstract base class
- Updated agent to use provider interface
- Added configuration for custom providers

Closes #123"
```

### 7. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
```

**Pull Request Template:**

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
How has this been tested?

## Checklist
- [ ] Code follows project style guidelines
- [ ] Added/updated tests
- [ ] All tests pass
- [ ] Updated documentation
- [ ] No breaking changes (or documented)
```

## Development Guidelines

### Project Structure

```
ask_shell/
├── agent.py          # Core agent logic
├── cli.py            # Command-line interface
├── llm/              # LLM integrations
├── executor/         # Command execution
├── models/           # Data models
└── ui/               # User interface
```

### Adding a New LLM Provider

1. Create new file in `ask_shell/llm/`:

```python
# ask_shell/llm/anthropic.py
from .base import LLMClient

class AnthropicClient(LLMClient):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def generate_command(self, task: str, context: dict) -> str:
        # Implementation
        pass
```

2. Register in `ask_shell/llm/__init__.py`:

```python
from .anthropic import AnthropicClient

def get_llm_client(provider: str = "openai"):
    if provider == "anthropic":
        return AnthropicClient(os.getenv("ANTHROPIC_API_KEY"))
    # ...
```

3. Add tests:

```python
# tests/test_llm_anthropic.py
def test_anthropic_client():
    client = AnthropicClient(api_key="test")
    # Test implementation
```

### Adding UI Components

Use Rich library for consistent styling:

```python
from rich.console import Console
from rich.panel import Panel

console = Console()

def display_command(command: str):
    panel = Panel(
        command,
        title="⚙️ Generated Command",
        border_style="blue"
    )
    console.print(panel)
```

### Safety Additions

To add new dangerous patterns:

```python
# In ask_shell/executor/shell.py
DANGEROUS_PATTERNS = [
    r'rm\s+-rf\s+/',
    r'your-new-pattern',  # Add here with comment
]
```

## Testing

### Test Structure

```
tests/
├── test_agent.py      # Agent tests
├── test_llm.py        # LLM client tests
├── test_executor.py   # Executor tests
└── fixtures/          # Test data
```

### Writing Tests

```python
import pytest
from alpha_bot.agent import TaskAgent

class TestAgent:
    def setup_method(self):
        """Setup before each test"""
        self.agent = TaskAgent(MockLLM(), MockExecutor())
    
    def test_simple_task(self):
        """Test description"""
        result = self.agent.execute_task("test task")
        assert result is not None
    
    @pytest.mark.parametrize("task,expected", [
        ("list files", "ls"),
        ("show processes", "ps"),
    ])
    def test_various_tasks(self, task, expected):
        """Test multiple scenarios"""
        command = self.agent.generate_command(task)
        assert expected in command
```

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_agent.py

# Specific test
pytest tests/test_agent.py::TestAgent::test_simple_task

# With coverage
pytest --cov=ask_shell --cov-report=html

# Verbose output
pytest -v
```

## Documentation

### Updating Documentation

Documentation is in `docs/` using MkDocs:

```bash
# Install docs dependencies
pip install mkdocs-material

# Serve locally
mkdocs serve

# Build
mkdocs build
```

### Documentation Style

- Use clear, concise language
- Include code examples
- Add screenshots/GIFs for UI changes
- Update navigation in `mkdocs.yml`

## Release Process

Maintainers follow this process for releases:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release branch: `git checkout -b release/v0.4.0`
4. Tag release: `git tag v0.4.0`
5. Push: `git push origin v0.4.0`
6. Create GitHub release
7. Publish to PyPI: `python -m build && twine upload dist/*`

## Getting Help

- **Questions**: Open a discussion on GitHub
- **Bugs**: Create an issue
- **Chat**: (Add Discord/Slack link if available)

## Recognition

Contributors will be recognized in:

- GitHub contributors page
- Release notes
- README.md (for significant contributions)

Thank you for contributing to Ask-Shell! 🚀
