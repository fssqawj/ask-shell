# Examples

Real-world examples demonstrating Ask-Shell's capabilities.

## Demo Videos

### Demo 1: Browser Control with Natural Language

Watch Ask-Shell control the terminal and browser with natural language commands.

![browser-demo](https://github.com/user-attachments/assets/717ce22f-084a-4081-8ad0-ae23f7daf0ff)

### Demo 2: Terminal Task Automation

See Ask-Shell handle complex multi-step terminal tasks automatically.

![ask-shell-demo](https://github.com/user-attachments/assets/8721876f-92db-4762-a03d-64d845546de0)

## Simple Examples

### File Management

**List specific files:**

```bash
ask "find all Python files modified in the last week"
```

**Search content:**

```bash
ask "search for the word 'TODO' in all markdown files"
```

**File information:**

```bash
ask "show me the 10 largest files in this directory"
```

## Multi-Step Examples

These examples showcase Ask-Shell's ability to handle complex workflows.

### Project Organization

**Task**: Organize a messy project directory

```bash
ask "organize this project: create folders for docs, tests, and src, then move files accordingly"
```

**What Ask-Shell does:**

```
Step 1: Analyze structure
  $ ls -la

Step 2: Create directories
  $ mkdir -p docs tests src

Step 3: Move Python files
  $ mv *.py src/

Step 4: Move documentation
  $ mv *.md docs/

Step 5: Move test files
  $ mv test_*.py tests/

Step 6: Verify organization
  $ tree -L 2

✓ Task complete!
```

### Development Workflow

**Task**: Prepare code for commit

```bash
ask "format all Python files with black, run tests, and if they pass, commit with a descriptive message"
```

**Execution:**

```
Step 1: Format code
  $ black *.py
  Formatted 5 files

Step 2: Run tests
  $ python -m pytest
  ========== 10 passed ==========

Step 3: Stage changes
  $ git add .

Step 4: Create commit
  $ git commit -m "Format code with black and ensure all tests pass"

✓ All steps completed successfully!
```

### System Maintenance

**Task**: Clean up old logs

```bash
ask "find all log files older than 30 days, show them to me, then archive them"
```

**Process:**

```
Step 1: Find old logs
  $ find /var/log -name "*.log" -mtime +30
  /var/log/old-app.log
  /var/log/service-2023.log

Step 2: Create archive
  $ tar -czf logs-archive-$(date +%Y%m%d).tar.gz /var/log/*.log

Step 3: Verify archive
  $ tar -tzf logs-archive-20240127.tar.gz

Step 4: Remove archived logs (with confirmation)
  $ rm /var/log/old-app.log /var/log/service-2023.log
  
✓ Archived and cleaned!
```

## Complex Examples

### Code Analysis

**Task**: Analyze codebase metrics

```bash
ask "count lines of code for each Python file, calculate total, and create a report"
```

**Output:**

```
Step 1: Count lines per file
  $ find . -name "*.py" -exec wc -l {} \;

Step 2: Calculate total
  $ find . -name "*.py" -exec cat {} \; | wc -l

Step 3: Generate report
  $ cat > code_metrics.txt << EOF
  Code Metrics Report
  Generated: $(date)
  
  Total Python files: 15
  Total lines of code: 2,458
  
  Files by size:
  - agent.py: 456 lines
  - cli.py: 234 lines
  ...
  EOF

✓ Report saved to code_metrics.txt
```

### Backup and Deployment

**Task**: Create backup before deployment

```bash
ask "create a timestamped backup of the current directory, then deploy to production"
```

**Workflow:**

```
Step 1: Create backup
  $ tar -czf backup-myapp-$(date +%Y%m%d-%H%M%S).tar.gz .

Step 2: Verify backup
  $ tar -tzf backup-myapp-20240127-143022.tar.gz | head -10

Step 3: Deploy (custom command)
  $ ./deploy.sh production

Step 4: Verify deployment
  $ curl -I https://myapp.com
  HTTP/1.1 200 OK

✓ Backup created and deployed!
```

### Git Workflow

**Task**: Complete git workflow

```bash
ask "check git status, stage all changes, commit with meaningful message based on changes, and push to origin"
```

**Execution:**

```
Step 1: Check status
  $ git status
  Modified: 3 files
  New: 2 files

Step 2: Review changes
  $ git diff --stat

Step 3: Stage changes
  $ git add .

Step 4: Analyze changes for commit message
  $ git diff --cached --stat
  
  💭 Changes: Added new user authentication module,
      updated configuration, added tests

Step 5: Commit
  $ git commit -m "Add user authentication module with tests and config"

Step 6: Push
  $ git push origin main

✓ Changes committed and pushed!
```

## Skill-Based Capabilities

Ask-Shell leverages a variety of skills to handle different types of tasks:

### LLM Skill

Handles traditional command generation, translation, summarization, and text processing tasks.

```bash
ask "translate this paragraph to French"
ask "summarize the content of this document"
ask "explain how this Python code works"
```

### Browser Integration

Control web browsers using natural language with Playwright automation.

```bash
ask "open GitHub in my browser"
ask "search Google for Python tutorials"
ask "extract product prices from this e-commerce website"
ask "take a screenshot of the current webpage"
```

### PPT Generation

Create presentations from natural language descriptions.

```bash
ask "create a presentation about climate change with 5 slides"
ask "make a PowerPoint about our quarterly results"
```

### Image Generation

Generate images based on text descriptions.

```bash
ask "create an image of a futuristic cityscape"
ask "generate a logo for a tech startup"
```

### WeChat Automation (macOS)

WeChat automation is available for macOS using GUI automation, but is currently disabled in the default configuration.

To enable it, uncomment the WeChat skill registration in the agent code.

```bash
# Once enabled, you can use commands like:
ask "send message 'Hello!' to contact 'John Doe' via WeChat"
ask "send message 'Meeting reminder' to group 'Team Alpha' via WeChat"
```

### Feishu Automation (macOS)

Automate Feishu/Lark messaging on macOS using GUI automation.

```bash
ask "send message 'Hello!' to contact 'Jane Smith' via Feishu"
ask "send message 'Daily report ready' to group 'Project Team' via Feishu"
```

### Direct LLM Processing

Perform direct language processing without command execution.

```bash
ask -l "translate this text to Spanish: Hello, how are you?"
ask -l "summarize this article in 3 bullet points"
ask -l "explain quantum computing in simple terms"
```

### Open Websites

```bash
ask "open GitHub in my default browser"
```

Platform-specific execution:

- **macOS**: `open https://github.com`
- **Linux**: `xdg-open https://github.com`
- **Windows**: `start https://github.com`

### Search Operations

```bash
ask "search Google for 'Python asyncio tutorial'"
```

Opens browser with Google search URL.

## Error Recovery Examples

### Failed Installation

**Task**: Install dependencies

```bash
ask "install project dependencies"
```

**With automatic retry:**

```
Attempt 1:
  $ pip install -r requirements.txt
  ❌ Error: pip: command not found

💭 Analyzing failure...
   pip not found, trying python -m pip

Attempt 2:
  $ python -m pip install -r requirements.txt
  ❌ Error: No module named pip

💭 Trying alternative...
   Installing pip first

Attempt 3:
  $ python -m ensurepip
  $ python -m pip install -r requirements.txt
  ✅ Success! Installed 15 packages

✓ Task completed after 3 attempts!
```

### Permission Issues

**Task**: Create log directory

```bash
ask "create a logs directory in /var/log"
```

**Auto-adjustment:**

```
Attempt 1:
  $ mkdir /var/log/myapp
  ❌ Error: Permission denied

💭 Analyzing: Need elevated permissions
   Asking user for sudo

Attempt 2:
  $ sudo mkdir /var/log/myapp
  [sudo] password:
  ✅ Directory created

✓ Adjusted strategy and succeeded!
```

## Interactive Mode Examples

### Exploratory Analysis

```
$ ask -i

Ask-Shell > list all files in current directory
[... shows file list ...]

Ask-Shell > how many Python files are there
💭 Context: Using file list from previous command
   Counting .py extensions

Ask-Shell > show me the largest one
💭 Remembering: Found agent.py is largest (456 lines)
   $ cat agent.py

Ask-Shell > summarize what it does
💭 Analyzing code from agent.py
   This is the main task automation agent...

Ask-Shell > exit
```

### Step-by-Step Task

```
$ ask -i

Ask-Shell > I want to deploy my app but first backup everything
💭 Breaking down: backup → deploy
   Starting with backup...

Ask-Shell > make the backup name include the git commit hash
💭 Adjusting backup command
   $ tar -czf backup-$(git rev-parse --short HEAD).tar.gz .

Ask-Shell > now deploy to staging first
   $ ./deploy.sh staging

Ask-Shell > verify it's working
   $ curl -I https://staging.myapp.com

Ask-Shell > looks good, deploy to production
   $ ./deploy.sh production

Ask-Shell > done
```

## Comparison Examples

### Shell-GPT vs Ask-Shell

**Task**: "Organize project files"

**Shell-GPT output:**

```
mkdir -p src tests docs
```

Stops here. You need to:

- Run the command manually
- Figure out how to move files
- Verify the result

**Ask-Shell output:**

```
Step 1: Create directories
  $ mkdir -p src tests docs

Step 2: Move Python files
  $ find . -maxdepth 1 -name "*.py" -exec mv {} src/ \;

Step 3: Move test files
  $ find src -name "test_*.py" -exec mv {} ../tests/ \;

Step 4: Move markdown docs
  $ mv *.md docs/

Step 5: Verify organization
  $ tree -L 2

✓ Project organized!
```

Fully automated, multi-step execution until complete!

## Real-World Use Cases

### 1. Daily Development Tasks

```bash
# Morning routine
ask "pull latest changes, install new dependencies, run tests"

# Code cleanup
ask "find all .pyc and __pycache__ folders and remove them"

# Pre-commit check
ask "run linting, fix auto-fixable issues, run tests"
```

### 2. System Administration

```bash
# Log analysis
ask "analyze last 1000 lines of syslog for errors and create summary"

# Disk cleanup
ask "find files larger than 1GB not accessed in 90 days"

# Security audit
ask "find all files with 777 permissions and list them"
```

### 3. Data Processing

```bash
# CSV processing
ask "convert all CSV files to JSON format"

# Image batch processing
ask "resize all images in this folder to 800x600"

# Log aggregation
ask "combine all .log files from subdirectories into one file"
```

### 4. Project Setup

```bash
# New Python project
ask "create a Python project structure with virtual environment, install common dependencies, and create README"

# Frontend setup
ask "initialize npm project, install React and common dependencies, create basic folder structure"
```

## Tips for Best Results

### Be Specific

❌ **Vague**: "do something with files"

✅ **Specific**: "find all JavaScript files and check for console.log statements"

### Describe the Goal

❌ **Too technical**: "run find -name '*.py' -exec wc -l"

✅ **Goal-oriented**: "count total lines of Python code in this project"

### Provide Context

❌ **No context**: "clean up"

✅ **With context**: "remove all log files older than 30 days from /var/log"

### Trust the Process

For complex tasks, let Ask-Shell work through multiple steps:

```bash
ask "audit this codebase for potential issues, create a report, and suggest fixes"
```

The AI will break it down intelligently and execute step by step!

## Next Steps

- [Learn about advanced features](advanced-features.md)
- [Understand safety mechanisms](safety.md)
- [Explore the API](../api/agent.md)
