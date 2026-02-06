# Memory System API

The memory system in Ask-Shell provides contextual awareness and learning capabilities that enhance task execution.

## Overview

The memory system maintains a contextual memory bank that stores execution history, enabling the AI to learn from previous steps and make informed decisions for subsequent actions. This allows for more coherent and context-aware task execution.

## Core Components

### MemoryBank Class

The [MemoryBank](file:///Users/anweijie/Documents/ask-shell/ask_shell/memory/bank.py) is the central component of the memory system.

#### Initialization

```python
from ask_shell.memory.bank import MemoryBank

# Create a memory bank with default settings
memory_bank = MemoryBank()

# Create a memory bank with custom settings
memory_bank = MemoryBank(max_entries=10, compression_threshold=5)
```

**Parameters:**
- `max_entries` (int): Maximum number of entries to keep before compression (default: 6)
- `compression_threshold` (int): Number of entries that triggers compression (default: 6)

#### Methods

##### `add_entry(entry: MemoryEntry)`

Add a memory entry to the bank.

**Parameters:**
- `entry` ([MemoryEntry](file:///Users/anweijie/Documents/ask-shell/ask_shell/memory/types.py)): MemoryEntry to add

```python
from ask_shell.memory.types import MemoryEntry

entry = MemoryEntry(
    skill_name="CommandSkill",
    thinking="Analyzing directory structure...",
    command="ls -la",
    result="Directory listing with 15 files",
    importance=0.7
)
memory_bank.add_entry(entry)
```

##### `get_relevant_memories(query: MemoryQuery) -> List[MemoryEntry]`

Retrieve relevant memories based on query criteria.

**Parameters:**
- `query` ([MemoryQuery](file:///Users/anweijie/Documents/ask-shell/ask_shell/memory/types.py)): MemoryQuery specifying retrieval criteria

**Returns:**
- List of relevant MemoryEntries

```python
from ask_shell.memory.types import MemoryQuery

query = MemoryQuery(
    keywords=["directory", "structure"],
    min_importance=0.5,
    max_results=5
)
relevant_memories = memory_bank.get_relevant_memories(query)
```

##### `get_recent_entries(count: int = 5) -> List[MemoryEntry]`

Get the most recent entries.

**Parameters:**
- `count` (int): Number of recent entries to return (default: 5)

**Returns:**
- List of recent MemoryEntries

##### `get_summaries() -> List[MemorySummary]`

Get all memory summaries.

**Returns:**
- List of MemorySummaries

##### `get_all_memories() -> List[MemoryEntry]`

Get all memory entries (both compressed and uncompressed).

**Returns:**
- List of all MemoryEntries

##### `clear()`

Clear all memories and summaries.

##### `get_stats() -> Dict[str, Any]`

Get statistics about the memory bank.

**Returns:**
- Dictionary with memory bank statistics

### Memory Types

The memory system defines several data types in [types.py](file:///Users/anweijue/Documents/ask-shell/ask_shell/memory/types.py):

#### MemoryEntry

Represents a single memory entry with metadata containing information from a skill execution step.

**Attributes:**
- `id` (str): Unique identifier for the entry
- `timestamp` (datetime): When the entry was created
- `skill_name` (str): Name of the skill that created the entry
- `thinking` (str): The AI's thinking process
- `command` (str): Command that was executed
- `result` (str): Result of the execution
- `summary` (str): Auto-generated summary
- `importance` (float): 0.0-1.0 rating of importance
- `tags` (List[str]): Keywords for categorization
- `step_number` (int): The step number in the task execution

#### MemorySummary

Represents a compressed summary of multiple memory entries.

**Attributes:**
- `id` (str): Unique identifier for the summary
- `timestamp` (datetime): When the summary was created
- `title` (str): Title of the summary
- `content` (str): Content of the summary
- `source_entries` (List[str]): IDs of entries that were summarized
- `tags` (List[str]): Tags from the summarized entries

#### MemoryQuery

Query parameters for retrieving memories.

**Attributes:**
- `keywords` (List[str]): Keywords to search for
- `min_importance` (float): Minimum importance threshold
- `max_results` (int): Maximum number of results to return
- `tags` (List[str]): Tags to filter by
- `date_from` (datetime): Earliest date to include
- `date_to` (datetime): Latest date to include

## Integration with Task Execution

The memory system is tightly integrated with the task execution flow:

1. After each skill execution, the result is automatically added to the memory bank
2. The memory bank is included in the context passed to the skill selector
3. Relevant memories are used to inform future skill selections and executions
4. Memory compression occurs automatically when thresholds are reached

## Usage in Skills

Skills can access the memory bank through the execution context:

```python
def execute(self, task: str, context: Optional[Dict[str, Any]] = None, **kwargs):
    # Get memory bank from context
    memory_bank = context.get('memory_bank')
    
    if memory_bank:
        # Get recent memories to inform this execution
        recent_memories = memory_bank.get_recent_entries(3)
        
        # Use memory to make better decisions
        # ... skill logic ...
    
    # The system automatically adds this execution to memory
    # after the skill completes
```

## Memory Compression

The system automatically compresses older memories when:
- The number of entries exceeds the compression threshold
- The memory bank reaches its maximum capacity

Compression creates summaries of groups of related entries, preserving important information while reducing memory usage.

## Best Practices

1. **Importance Rating**: Assign appropriate importance ratings to ensure important memories are retained
2. **Tagging**: Use descriptive tags to enable efficient retrieval of related memories
3. **Context Utilization**: Leverage existing memories to make more informed decisions
4. **Memory Cleanup**: Clear memory banks when starting new unrelated tasks to avoid irrelevant context

## Example Implementation

```python
from ask_shell.memory.bank import MemoryBank
from ask_shell.memory.types import MemoryEntry, MemoryQuery

# Initialize memory bank
memory_bank = MemoryBank(max_entries=10, compression_threshold=5)

# Add entries during task execution
entry1 = MemoryEntry(
    skill_name="CommandSkill",
    thinking="Need to check current directory",
    command="pwd",
    result="/home/user/project",
    importance=0.8,
    tags=["filesystem", "location"]
)
memory_bank.add_entry(entry1)

# Later in execution, retrieve relevant memories
query = MemoryQuery(
    keywords=["directory", "location"],
    min_importance=0.5
)
relevant_memories = memory_bank.get_relevant_memories(query)

# Use retrieved memories to inform next steps
for memory in relevant_memories:
    print(f"Previous action: {memory.command} -> {memory.result}")
```

The memory system enables Ask-Shell to maintain context across multiple steps of complex tasks, resulting in more intelligent and coherent task execution.