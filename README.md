# Ask-Shell

[![PyPI version](https://img.shields.io/pypi/v/askshell-ai.svg)](https://pypi.org/project/askshell-ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

[中文](README_zh.md) | English

Control your terminal with natural language - Let AI generate and execute shell commands for you.

## 📖 Overview

Ask-Shell is an AI-powered intelligent terminal assistant that understands your natural language descriptions and automatically generates and executes corresponding shell commands. No need to memorize complex command syntax - just describe what you want to do in plain language, and leave the rest to AI.

### Features

- 🤖 **Natural Language Interaction** - Describe tasks in plain language, AI generates commands automatically
- 🔒 **Safety Confirmation** - Dangerous operations are automatically identified and require confirmation
- 🎯 **Multiple Running Modes** - Supports single execution, interactive mode, and auto mode
- 🎨 **Beautiful Interface** - Rich terminal output using Rich library with real-time animation effects
- ⚡ **Real-time Feedback** - AI thinking process displayed in real-time, command execution with animations
- 🔄 **Smart Retry** - AI tries alternative solutions when command execution fails
- 🧪 **Demo Mode** - Experience features without API Key

## 🎬 Demo

![browser-demo](https://github.com/user-attachments/assets/717ce22f-084a-4081-8ad0-ae23f7daf0ff)

<p align="center"><em>Demo 1: Using ask-shell to control terminal with natural language</em></p>

![ask-shell-demo](https://github.com/user-attachments/assets/8721876f-92dc-4762-a03d-64d845546de0)

<p align="center"><em>Demo 2: Using ask-shell to control terminal with natural language</em></p>

Ask-Shell provides a beautiful terminal interface with real-time feedback:

- 💭 **Real-time Thinking Process** - See AI's thought process
- ⚙️ **Command Execution Animation** - Dynamic loading effects during command execution
- ✨ **Syntax Highlighting** - Generated commands with syntax highlighting
- 📊 **Structured Output** - Clear panels and icon displays
- 🎯 **Interactive Confirmation** - Dangerous operations with clear warning indicators

## 🚀 Quick Start

### Installation

#### Method 1: Development Mode (Recommended)

```bash
# Clone the repository
git clone https://github.com/fssqawj/ask-shell.git
cd ask-shell

# Install in development mode (can use ask-shell or ask command directly)
pip install -e .
```

#### Method 2: Install from PyPI

```bash
pip install askshell-ai
```

#### Method 3: Install Dependencies Only

```bash
pip install -r requirements.txt
```

### Configure API Key

1. Copy the environment variable template:
```bash
cp .env.example .env
```

2. Edit the `.env` file and fill in your OpenAI API Key:
```bash
OPENAI_API_KEY=your-api-key-here
```

## 💡 Usage

### After Installation (Recommended)

If you installed with `pip install -e .` or `pip install askshell-ai`, you can use commands directly:

```bash
# Use ask-shell command
ask-shell "list all Python files in current directory"

# Or use the shorter ask command
ask "list all Python files in current directory"

# Interactive mode
ask -i

# Demo mode (no API Key required)
ask -d "create a test folder"

# Auto execution mode (no confirmation needed for each command)
ask -a "count lines of code in current directory"

# Specify working directory
ask -w /path/to/dir "your task"
```

### Direct Run (Without Installation)

```bash
# Single task execution
python ask_shell/cli.py "list all Python files in current directory"

# Interactive mode
python ask_shell/cli.py -i

# Demo mode (no API Key required)
python ask_shell/cli.py -d "create a test folder"

# Auto execution mode
python ask_shell/cli.py -a "count lines of code in current directory"

# Specify working directory
python ask_shell/cli.py -w /path/to/dir "your task"
```

### Examples

The following examples work with both `ask` command and `python ask_shell/cli.py`:

```bash
# File operations
ask "find all files larger than 1MB"
ask "create a folder named backup and copy all .py files into it"

# System information
ask "check system memory usage"
ask "list all running Python processes"

# Git operations
ask "commit all changes with message 'update code'"
ask "show last 5 commit logs"

# Text processing
ask "count total lines of all .py files"
ask "search for lines containing 'error' in all .txt files"

# Browser operations
ask "open GitHub in default browser"
ask "open Google and search for Python tutorial"
ask "open local file index.html in Chrome browser"
```

### Interactive Mode

```bash
ask -i
# or
python ask_shell/cli.py -i
```

In interactive mode, you can continuously input tasks:
```
Ask-Shell > list files in current directory
Ask-Shell > create a test file
Ask-Shell > exit  # Exit
```

## 📁 Project Structure

```
ask-shell/
├── ask_shell/           # Core code
│   ├── agent.py        # Main logic
│   ├── executor/       # Command executor
│   ├── llm/            # LLM client
│   ├── models/         # Data models
│   └── ui/             # User interface
├── requirements.txt    # Dependencies
└── .env.example        # Environment variable template
```

## ⚙️ Configuration Options

### Environment Variables

You can configure the following options in the `.env` file:

```bash
# OpenAI API Key (required)
OPENAI_API_KEY=your-api-key-here

# Custom API URL (optional, for compatible APIs)
OPENAI_API_BASE=https://api.openai.com/v1

# Model name (optional, default: gpt-4)
MODEL_NAME=gpt-4
```

### Command Line Arguments

- `task` - Task description to execute
- `-i, --interactive` - Interactive mode
- `-a, --auto` - Auto execution mode (no confirmation needed)
- `-d, --demo` - Demo mode (no API Key required)
- `-w, --workdir` - Specify working directory

## 🔒 Safety Features

Ask-Shell has built-in safety mechanisms:

1. **Dangerous Operation Detection** - AI identifies potentially dangerous commands
2. **Auto Confirmation Prompt** - Dangerous operations require user confirmation
3. **Command Editing** - Users can edit commands before execution
4. **Skip Option** - Users can skip commands they don't want to execute

## 🛠️ Tech Stack

- **Python 3.7+**
- **OpenAI API** - GPT-4 model
- **Rich** - Beautiful terminal output
- **python-dotenv** - Environment variable management

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Issues and Pull Requests are welcome!
