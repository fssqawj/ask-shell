## Advanced Features

Unlock the full potential of Ask-Shell with these advanced features.

Ask-Shell's architecture is built around a flexible skill system that enables various types of task execution:

- **Command Skill**: Traditional command generation and text processing
- **Direct LLM Skill**: Translation, summarization, and analysis without command execution
- **Browser Skill**: Web automation using Playwright with anti-bot detection
- **PPT Skill**: Presentation generation from natural language
- **Image Skill**: Image generation capabilities
- **WeChat Skill**: WeChat automation for macOS (GUI automation) - *currently disabled*
- **Feishu Skill**: Feishu/Lark automation for macOS (GUI automation)
- **Extensible Skills**: Plugin-ready architecture for adding new capabilities

## Multi-Step Task Execution

### How It Works

Ask-Shell uses an **agent loop pattern** that continuously executes until your task is complete:

```
1. Analyze task → 2. Generate command → 3. Execute → 4. Analyze results → 
5. Decide next step → (Loop back to 2 if needed) → 6. Task complete
```

### Example: Complex Organization

```bash
ask "organize this project: create proper folder structure, move files, and create documentation"
```

The agent will:

**Step 1**: Analyze current structure

```
find . -type f -name "*" | head -20
```

**Step 2**: Create folders

```
mkdir -p {docs,tests,src,config}
```

**Step 3**: Move Python files

```
mv *.py src/
```

**Step 4**: Move configuration files

```
mv *.yml *.json config/
```

**Step 5**: Create documentation

```
echo "# Project Structure" > docs/structure.md
tree -L 2 >> docs/structure.md
```

**Step 6**: Verify organization

```
tree -L 2
```

All automatically, with your confirmation at each step!

## Intelligent Error Recovery

### Auto-Retry with Strategy Adjustment

When a command fails, Ask-Shell doesn't just stop - it analyzes and adapts.

**Example Scenario:**

```bash
ask "install project dependencies and run tests"
```

**If pip install fails:**

```
💭 First attempt failed: pip not found
   Analyzing error...
   Trying alternative: python -m pip install
```

**If tests require setup:**

```
💭 Tests failed: module not found
   Analyzing error...
   Installing missing dependency first...
```

### Failure Analysis

The AI examines:

- Error messages
- Exit codes
- Context from previous steps
- Alternative approaches

Then decides:

- Should it retry with modifications?
- Is there an alternative command?
- Does it need a preparatory step?
- Should it ask for user guidance?

## Context Awareness

### Conversation History

In interactive mode, Ask-Shell maintains full context:

```
Ask-Shell > find all Python files
[... lists 10 files ...]

Ask-Shell > check which ones were modified today
💭 Remembering: We found 10 Python files in previous step
   Filtering those files by modification date...

Ask-Shell > show me the contents of the most recently modified one
💭 Context: Previous command identified 3 files modified today
   Opening the most recent: app.py
```

### Task Context

The agent tracks:

- Files discovered
- Commands executed
- Results obtained
- Current working directory
- Previous failures and successes

## Advanced Command Composition

### Chaining Operations

```bash
ask "find all log files, grep for errors, count occurrences, and sort by frequency"
```

Results in sophisticated pipeline:

```bash
find . -name "*.log" -exec grep -h "ERROR" {} \; | sort | uniq -c | sort -rn
```

### Complex Conditions

```bash
ask "find files larger than 10MB but smaller than 100MB, modified in last week, excluding node_modules"
```

Generates:

```bash
find . -type f -size +10M -size -100M -mtime -7 -not -path "*/node_modules/*"
```

## Browser Integration

### Opening URLs

```bash
ask "open GitHub in browser"
ask "search Google for Python best practices"
```

### Platform-Specific Commands

Ask-Shell detects your OS and uses the correct command:

- macOS: `open`
- Linux: `xdg-open`
- Windows: `start`

## Working with Git

### Intelligent Commit Messages

```bash
ask "commit all changes with a meaningful message based on what changed"
```

The AI will:

1. Check `git diff` or `git status`
2. Analyze the changes
3. Generate descriptive commit message
4. Execute commit

### Complex Git Workflows

```bash
ask "create a new branch, commit changes, push, and create a pull request template"
```

## Dangerous Operation Handling

### Dual-Layer Safety

**Layer 1: AI Analysis**

```bash
ask "clean up old files"
```

```
⚠️ DANGER DETECTED
   Command: rm -rf old_files/
   
   Why dangerous: Recursive deletion cannot be undone
   Recommendation: Use -i flag for confirmation on each file
                  Or: Move to trash instead
   
   Proceed? [y/N]:
```

**Layer 2: Blacklist**

Hardcoded protection against catastrophic commands:

- `rm -rf /`
- `dd if=/dev/zero of=/dev/sda`
- `:(){ :|:& };:` (fork bomb)
- Direct `/dev` manipulation

### Interactive Editing

When warned, you can:

```
⚠️ Dangerous command detected
   Command: rm -rf *.log
   
   [E]dit / [S]kip / [Q]uit / Force [Y]es:
```

Choose **E** to modify:

```
Edit command: rm -i *.log  # Much safer!
```

## Custom Working Environments

### Virtual Environment Awareness

```bash
ask "activate virtual environment and run tests"
```

AI detects and uses:

- `venv/bin/activate`
- `source .env/bin/activate`
- `pipenv shell`
- `conda activate`

### Project-Specific Commands

```bash
ask "run the project's start command"
```

AI checks:

- `package.json` scripts
- `Makefile` targets
- `pyproject.toml` scripts
- `docker-compose.yml`

## Performance Optimization

### Parallel Execution Hints

For safe, independent operations:

```bash
ask "check file counts in all subdirectories"
```

Could potentially parallelize (future feature):

```bash
find . -maxdepth 1 -type d -exec sh -c 'echo -n "{}: "; find {} -type f | wc -l' \;
```

### Efficient Pipelines

AI optimizes command combinations:

**Instead of:**

```bash
cat file.txt | grep "error" | grep "critical" | wc -l
```

**Generates:**

```bash
grep -c "error.*critical" file.txt
```

## Integration Patterns

### With CI/CD

```bash
ask -a -w /var/ci/project "run tests and generate coverage report"
```

### With Cron Jobs

```bash
# In cron:
0 2 * * * cd /backups && ask -a "compress and archive yesterday's logs"
```

### With Monitoring

```bash
ask "check if any processes are using more than 80% CPU and log them"
```

## Extending Ask-Shell

### Custom LLM Providers

Configure alternative APIs:

```bash
export OPENAI_API_BASE=http://localhost:11434/v1  # Ollama
export MODEL_NAME=llama2
```

### Adding Custom Safety Rules

Edit the executor to add project-specific safety rules:

```python
# In executor/shell.py
CUSTOM_BLACKLIST = [
    'drop database',
    'truncate table',
    # Your patterns
]
```

## Advanced Configuration

### Model Selection Strategy

**For complex tasks:**

```bash
export MODEL_NAME=gpt-4
```

**For simple, fast tasks:**

```bash
export MODEL_NAME=gpt-3.5-turbo
```

### Timeout Configuration

For long-running operations, increase timeout (future feature):

```bash
export COMMAND_TIMEOUT=300  # 5 minutes
```

## Debugging and Logging

### Verbose Mode

See detailed AI reasoning (future feature):

```bash
ask --verbose "complex task"
```

### Conversation Export

Save interaction history:

```bash
ask -i --export-conversation session.json
```

## Best Practices for Advanced Usage

### 1. Task Decomposition

For very complex tasks, help the AI by breaking down:

```bash
# Instead of one mega-task, use interactive mode:
ask -i

Ask-Shell > first, analyze the project structure
Ask-Shell > now organize into folders  
Ask-Shell > finally, create documentation
```

### 2. Verification Steps

Build verification into your tasks:

```bash
ask "migrate database schema and verify all tables exist"
```

### 3. Rollback Preparation

For risky operations:

```bash
ask "create backup, then modify configuration files"
```

## Next Steps

- [Learn about safety features in detail](safety.md)
- [See real-world examples](examples.md)
- [Explore API reference](../api/agent.md)
