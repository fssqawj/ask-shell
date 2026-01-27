# Ask-Shell

用自然语言操控你的终端 - 让 AI 帮你生成并执行 Shell 命令

## 📖 项目简介

Ask-Shell 是一个基于 AI 的智能终端助手，它能理解你的自然语言描述，自动生成并执行相应的 Shell 命令。无需记忆复杂的命令语法，只需用人话描述你想做什么，剩下的交给 AI。

### 特性

- 🤖 **自然语言交互** - 用人话描述任务，AI 自动生成命令
- 🔒 **安全确认机制** - 危险操作会自动识别并要求确认
- 🎯 **多种运行模式** - 支持单次执行、交互模式、自动模式
- 🎨 **美观的界面** - 使用 Rich 库提供丰富的终端输出，带有实时动画效果
- ⚡ **实时反馈** - AI 思考过程实时显示，命令执行带有动画效果
- 🔄 **智能重试** - 命令执行失败时，AI 会尝试其他方案
- 🧪 **演示模式** - 无需 API Key 即可体验功能

## 🎬 效果展示

<!-- 
请在 GitHub 编辑此 README 时，将视频拖拽到下方区域：
1. 点击 GitHub 上的编辑按钮
2. 将 ask-shell-demo.mp4 拖拽到编辑器中
3. GitHub 会自动上传并生成链接
-->

<p align="center"><em>演示：使用 ask-shell 通过自然语言操控终端</em></p>

Ask-Shell 提供了美观的终端界面和实时反馈：

- 💭 **思考过程实时显示** - 看到 AI 的思考过程
- ⚙️ **命令执行动画** - 执行命令时显示动态加载效果
- ✨ **语法高亮** - 生成的命令带有语法高亮
- 📊 **结构化输出** - 清晰的面板和图标显示
- 🎯 **交互式确认** - 危险操作带有明显的警告标识

## 🚀 快速开始

### 安装

#### 方式一：开发模式安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/fssqawj/ask-shell.git
cd ask-shell

# 以开发模式安装（可以直接使用 ask-shell 或 ask 命令）
pip install -e .
```

#### 方式二：直接安装依赖

```bash
pip install -r requirements.txt
```

### 配置 API Key

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的 OpenAI API Key：
```bash
OPENAI_API_KEY=your-api-key-here
```

## 💡 使用方法

### 安装后使用（推荐）

如果你使用 `pip install -e .` 安装，可以直接使用命令：

```bash
# 使用 ask-shell 命令
ask-shell "列出当前目录下的所有 Python 文件"

# 或者使用更短的 ask 命令
ask "列出当前目录下的所有 Python 文件"

# 交互模式
ask -i

# 演示模式（无需 API Key）
ask -d "创建一个测试文件夹"

# 自动执行模式（不需要确认每条命令）
ask -a "统计当前目录代码行数"

# 指定工作目录
ask -w /path/to/dir "你的任务"
```

### 直接运行（未安装时）

```bash
# 单次执行任务
python main.py "列出当前目录下的所有 Python 文件"

# 交互模式
python main.py -i

# 演示模式（无需 API Key）
python main.py -d "创建一个测试文件夹"

# 自动执行模式（不需要确认每条命令）
python main.py -a "统计当前目录代码行数"

# 指定工作目录
python main.py -w /path/to/dir "你的任务"
```

### 示例

以下示例同时适用于 `ask` 命令和 `python main.py`：

```bash
# 文件操作
ask "找出所有大于 1MB 的文件"
ask "创建一个名为 backup 的文件夹并复制所有 .py 文件进去"

# 系统信息
ask "查看系统内存使用情况"
ask "列出所有正在运行的 Python 进程"

# Git 操作
ask "提交所有更改，提交信息为 'update code'"
ask "查看最近 5 次提交记录"

# 文本处理
ask "统计所有 .py 文件的总行数"
ask "在所有 .txt 文件中搜索包含 'error' 的行"

# 浏览器操作
ask "用默认浏览器打开 GitHub"
ask "打开百度搜索 Python 教程"
ask "用 Chrome 浏览器打开本地文件 index.html"
```

### 交互模式

```bash
ask -i
# 或
python main.py -i
```

进入交互模式后，可以持续输入任务：
```
Ask-Shell > 列出当前目录下的文件
Ask-Shell > 创建一个测试文件
Ask-Shell > exit  # 退出
```

## 📁 项目结构

```
ask-shell/
├── ask_shell/           # 核心代码
│   ├── agent.py        # 主要逻辑
│   ├── executor/       # 命令执行器
│   ├── llm/            # LLM 客户端
│   ├── models/         # 数据模型
│   └── ui/             # 用户界面
├── main.py             # 入口程序
├── requirements.txt    # 依赖列表
└── .env.example        # 环境变量模板
```

## ⚙️ 配置选项

### 环境变量

在 `.env` 文件中可以配置以下选项：

```bash
# OpenAI API Key（必需）
OPENAI_API_KEY=your-api-key-here

# 自定义 API 地址（可选，用于兼容的 API）
OPENAI_API_BASE=https://api.openai.com/v1

# 模型名称（可选，默认：gpt-4）
MODEL_NAME=gpt-4
```

### 命令行参数

- `task` - 要执行的任务描述
- `-i, --interactive` - 交互模式
- `-a, --auto` - 自动执行模式（不需要确认）
- `-d, --demo` - 演示模式（不需要 API Key）
- `-w, --workdir` - 指定工作目录

## 🔒 安全特性

Ask-Shell 内置安全机制：

1. **危险操作识别** - AI 会判断命令是否具有危险性
2. **自动确认提示** - 危险操作会要求用户确认
3. **命令编辑** - 用户可以在执行前编辑命令
4. **跳过选项** - 用户可以跳过不想执行的命令

## 🛠️ 技术栈

- **Python 3.7+**
- **OpenAI API** - GPT-4 模型
- **Rich** - 美观的终端输出
- **python-dotenv** - 环境变量管理

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
