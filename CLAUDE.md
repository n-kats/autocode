# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Lint code
make lint
# or
ruff check nk_autocode samples
mypy nk_autocode samples

# Format code  
make format
# or
ruff format nk_autocode samples
ruff check --fix nk_autocode samples

# Run tests
make test
# or
pytest
```

## Architecture Overview

This is **nk-autocode**, a runtime code generation library that generates Python functions dynamically using AI (OpenAI API). The library allows developers to describe functions in natural language and have them automatically generated and executed at runtime.

### Key Components

**Core Framework (`nk_autocode/framework.py`)**
- `BaseAgent`: Abstract base for AI code generation agents
- `BaseAssistant`: Abstract base for assistant implementations  
- `Context`: Contains all information needed for code generation (description, args, types, etc.)
- `Variable`: Represents function parameters with type information
- `Feedback`: Error and human feedback for iterative code improvement

**Assistant System (`nk_autocode/presets/assistant.py`)**
- `Assistant`: Main orchestrator that manages the code generation workflow
- `Workspace`: Handles caching system with two storage strategies:
  - ID-based caching: `_cache/autocode/ids/{uuid}.py`
  - Structure-based caching: `_cache/autocode/structure/{path}/{name}.py`
- Supports interactive editing via external editors (configured via `EDITOR` env var)
- Implements feedback loops for error handling and human review

**Agent Implementations**
- `OpenAIAgent` (`nk_autocode/presets/openai_agent.py`): Uses OpenAI API for code generation
- Agents can be swapped via the `agent` parameter

**Public API (`nk_autocode/presets/default.py`)**
- `autocode()`: Main function for generating code from descriptions
- `setup_autocode()`: Global configuration (API keys, modes, defaults)
- `return_value()`, `print_and_exception()`: Dry-run helper functions

### Code Generation Workflow

1. **Context Creation**: Parse function description, arguments, and types into a `Context` object
2. **Cache Check**: Look for existing generated code by ID or file path + function name
3. **Generation Loop**: 
   - Generate code using the configured agent
   - Optionally show to user for interactive review/editing
   - Compile and validate the generated code
   - Handle errors with feedback and regeneration
4. **Caching**: Save successful code to workspace cache
5. **Return**: Compiled function ready for execution

### Usage Patterns

**Function Generation**: `autocode("description", args=["a", "b"])`
**Decorator Usage**: `@autocode(decorator=True)` with typed function signatures
**Dry Run Mode**: Test without AI generation using mock functions
**Interactive Mode**: Human review and editing of generated code before execution

## Environment Variables

- `OPENAI_API_KEY`: Required for OpenAI-based code generation
- `EDITOR`: Optional editor command for interactive code editing

## Cache Structure

Generated code is cached in `_cache/autocode/` to avoid regenerating identical functions:
- Functions with explicit IDs: `ids/{uuid}.py`
- Functions identified by location: `structure/{relative_path}/{function_name}.py`