# Skills System API

The skills system in Ask-Shell provides a flexible architecture for extending capabilities and automating various types of tasks.

## Overview

The skills system enables Ask-Shell to handle diverse tasks through specialized skill modules. Each skill is designed for specific types of operations, and the system intelligently selects the appropriate skill for each task step.

## Core Components

### Base Skill Class

All skills inherit from the [BaseSkill](file:///Users/anweijie/Documents/ask-shell/ask_shell/skills/base_skill.py) class which provides the common interface for skill execution.

#### Key Methods

##### `execute(task: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> SkillExecutionResponse`

Execute the skill for the given task.

**Parameters:**
- `task` (str): The task to execute
- `context` (Dict): Execution context containing history, memory, etc.
- `**kwargs`: Additional parameters

**Returns:**
- [SkillExecutionResponse](file:///Users/anweijie/Documents/ask-shell/ask_shell/models/types.py): The result of skill execution

### Skill Manager

The [SkillManager](file:///Users/anweijie/Documents/ask-shell/ask_shell/skills/skill_manager.py) handles registration, selection, and execution of skills.

#### Initialization

```python
from ask_shell.skills.skill_manager import SkillManager

# Create a skill manager with UI and persistence enabled
skill_manager = SkillManager(ui=console_ui, enable_persistence=True)
```

#### Methods

##### `register_skill()`

Register all built-in skills including CommandSkill, DirectLLMSkill, BrowserSkill, etc.

##### `register_dynamic_skill()`

Register dynamic skills from markdown files, attempting to load from persisted versions first.

##### `select_skill(task: str, context: Optional[Dict[str, Any]] = None) -> Optional[SkillSelectResponse]`

Select the best skill for the given task using LLM-based intelligent selection.

**Parameters:**
- `task` (str): The task description
- `context` (Dict): Optional context for decision making

**Returns:**
- [SkillSelectResponse](file:///Users/anweijie/Documents/ask-shell/ask_shell/models/types.py): Contains selected skill and selection information

##### `execute(task: str, context: Optional[Dict[str, Any]] = None) -> SkillResponse`

Execute a task using the appropriate skill.

**Parameters:**
- `task` (str): The task to execute
- `context` (Dict): Execution context

**Returns:**
- [SkillResponse](file:///Users/anweijie/Documents/ask-shell/ask_shell/models/types.py): The skill execution result

## Auto-Generated Persistent Skills

Ask-Shell features a dynamic skill generation system that allows skills to be automatically created from markdown descriptions and persistently stored.

### Skill Generator

The [SkillGenerator](file:///Users/anweijie/Documents/ask-shell/ask_shell/skills/skill_generator.py) creates skill classes from markdown descriptions.

#### Usage

```python
from ask_shell.skills.skill_generator import SkillGenerator

# Create a generator with persistence enabled
generator = SkillGenerator(enable_persistence=True)

# Parse a markdown description to create a skill
markdown_text = """
# My Custom Skill
This skill performs custom operations on files.

## Capabilities
- File processing
- Data extraction
- Report generation

## Examples
Process CSV files and extract summary statistics.
"""

skill_class = generator.parse_markdown_to_skill(markdown_text, "MyCustomSkill")
```

### Skill Persistence

The [SkillPersistence](file:///Users/anweijie/Documents/ask-shell/ask_shell/skills/skill_persistence.py) module handles saving and loading generated skills as Python files.

#### Methods

##### `save_skill_class(skill_class: Type[BaseSkill], skill_name: str) -> bool`

Save a skill class as a Python file.

**Parameters:**
- `skill_class` (Type[BaseSkill]): The skill class to save
- `skill_name` (str): Name of the skill

**Returns:**
- bool: True if saved successfully, False otherwise

##### `load_skill_class(skill_name: str) -> Optional[Type[BaseSkill]]`

Load a skill class from a Python file.

**Parameters:**
- `skill_name` (str): Name of the skill to load

**Returns:**
- Type[BaseSkill]: Skill class if loaded successfully, None otherwise

##### `skill_exists(skill_name: str) -> bool`

Check if a skill file exists for the given skill name.

## Built-in Skills

### Command Skill

[CommandSkill](file:///Users/anweijie/Documents/ask-shell/ask_shell/skills/command_skill.py) handles traditional command generation and text processing.

### Direct LLM Skill

[DirectLLMSkill](file:///Users/anweijie/Documents/ask-shell/ask_shell/skills/direct_llm_skill.py) handles tasks like translation, summarization, and analysis without command execution.

### Browser Skill

[BrowserSkill](file:///Users/anweijie/Documents/ask-shell/ask_shell/skills/browser_skill.py) provides web automation using Playwright with anti-bot detection.

### Special Features in Browser Skill

The BrowserSkill includes a hints system that reads markdown files from the `hints` directory:

```python
def _build_hints_info(self) -> str:
    """Read all markdown files from the hints folder and concatenate their content."""
    import os
    import glob
    
    hints_dir = os.path.join(os.path.dirname(__file__), "hints")
    md_files = glob.glob(os.path.join(hints_dir, "**", "*.md"), recursive=True)
    
    all_content = []
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                all_content.append(f"--- Content from {os.path.relpath(md_file, hints_dir)} ---\n{content}\n")
        except Exception as e:
            print(f"Warning: Could not read {md_file}: {e}")
    
    return "Information extraction suggestions:\n" + "\n".join(all_content) if all_content else ""
```

## Creating Custom Skills

To create a custom skill, extend the BaseSkill class:

```python
from ask_shell.skills.base_skill import BaseSkill, SkillExecutionResponse
from typing import List, Optional, Dict, Any

class MyCustomSkill(BaseSkill):
    def __init__(self):
        super().__init__()
        # Initialize skill-specific attributes
        self.name = "MyCustomSkill"
        # Define system prompt for LLM guidance
        self.system_prompt = "You are an expert at performing custom operations..."
    
    def get_capabilities(self) -> List[str]:
        return ["custom_operation", "data_processing"]
    
    def get_description(self) -> str:
        return "Performs custom operations based on user requests"
    
    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SkillExecutionResponse:
        # Implement skill logic here
        # Use context to access history, memory, etc.
        # Return a SkillExecutionResponse
        return SkillExecutionResponse(
            thinking="Processing custom task...",
            command="echo 'Custom operation completed'",
            explanation="Executed custom operation as requested"
        )
    
    def reset(self):
        # Clean up skill state if needed
        pass
```

## Skill Hints System

Skills can utilize contextual hints to improve execution quality. The hints system allows for domain-specific guidance and best practices that help skills perform more effectively in complex scenarios.

### Implementation

Skills can implement a `_build_hints_info()` method to load and incorporate hints:

```python
def _build_hints_info(self) -> str:
    """Load and return hints content to be included in the LLM prompt."""
    # Implementation depends on the skill's needs
    # Typically loads markdown files from a hints directory
    pass
```

The hints content is then included in the user message to the LLM during skill execution, providing additional context and guidance.

## Dynamic Skill Registration

The system first attempts to load skills from persisted Python files before generating from markdown:

```python
def register_dynamic_skill(self):
    """Register dynamic skills"""
    skill_generator = SkillGenerator(enable_persistence=self.enable_persistence)
    custom_skills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_skills")
    
    for file_name in os.listdir(custom_skills_dir):
        if file_name.endswith(".md"):
            skill_name = file_name[:-3]
            
            # Try to load from persisted Python file first
            skill = None
            if self.enable_persistence and self.persistence:
                if self.persistence.skill_exists(skill_name):
                    skill_class = self.persistence.load_skill_class(skill_name)
                    if skill_class:
                        skill = skill_class()
            
            # If not loaded from file, generate from markdown
            if skill is None:
                file_content = open(os.path.join(custom_skills_dir, file_name), "r", encoding="utf-8").read()
                skill = skill_generator.parse_markdown_to_skill(file_content, skill_name)
            
            self.skills.append(skill)
```

## Best Practices

1. **Skill Selection**: Use the SkillManager's intelligent selection rather than manually choosing skills
2. **Context Utilization**: Leverage the execution context to access history, memory, and other relevant information
3. **Persistence**: Enable skill persistence to avoid regenerating skills unnecessarily
4. **Hints**: Implement hints systems for skills that benefit from domain-specific guidance
5. **Error Handling**: Implement robust error handling in skill execution
6. **Capability Descriptions**: Clearly define skill capabilities to enable proper selection

## Execution Flow

The skill execution flow follows this pattern:

1. Task received by SkillManager
2. Intelligent skill selection using LLM
3. Selected skill executes with provided context
4. Skill response returned and processed
5. Execution result stored in memory for future reference
6. Task completion determined based on skill response

This architecture allows Ask-Shell to handle diverse tasks while maintaining context and learning from previous executions.