# One Function To Call Them All

A unified interface for interacting with multiple Language Model providers through a single, easy-to-use function.

## Overview

This project provides a streamlined way to interact with different LLM providers including:
- OpenAI (default model: gpt-4o)
- Anthropic (default model: claude-3-5-sonnet-latest)
- OpenRouter (default model: google/gemini-flash-1.5-8b)
- Groq (default model: llama-3.3-70b-versatile)

## Files Structure

- `one_function_to_call_them_all.py`: Core function that handles API calls to different providers
- `chat_interface.py`: Interactive CLI for chatting with different providers
- `requirements.txt`: Project dependencies
- `test_llm_handler.py`: Unit tests for the core functionality

## Setup

1. Install Dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables for API keys:
```bash
# For Windows
set OPENAI_API_KEY=your_key_here
set ANTHROPIC_API_KEY=your_key_here
set OPENROUTER_API_KEY=your_key_here
set GROQ_API_KEY=your_key_here

# For Linux/Mac
export OPENAI_API_KEY=your_key_here
export ANTHROPIC_API_KEY=your_key_here
export OPENROUTER_API_KEY=your_key_here
export GROQ_API_KEY=your_key_here
```

## Usage

### Interactive Chat Interface

Run the chat interface:
```bash
python chat_interface.py
```

Commands available in chat:
- `--switch`: Switch between different LLM providers
- `--exit`: End the chat session

### Programmatic Usage

```python
import asyncio
from one_function_to_call_them_all import one_function_to_call_them_all

async def example():
    messages = [
        {"role": "user", "content": "Hello, how are you?"}
    ]
    
    # Using OpenAI (default)
    response = await one_function_to_call_them_all(messages)
    
    # Using Anthropic
    response = await one_function_to_call_them_all(
        messages,
        provider="anthropic",
        system_message="You are a helpful assistant"
    )
    
    # Using OpenRouter
    response = await one_function_to_call_them_all(
        messages,
        provider="openrouter"
    )
    
    # Using Groq
    response = await one_function_to_call_them_all(
        messages,
        provider="groq"
    )

# Run the example
asyncio.run(example())
```

## Features

### Core Function (`one_function_to_call_them_all.py`)
- Unified interface for multiple LLM providers
- Proper error handling with descriptive messages
- Support for system messages
- Configurable parameters (max_tokens, additional provider-specific params)
- Color-coded console output for better visibility
- Async implementation for better performance

### Chat Interface (`chat_interface.py`)
- Interactive command-line interface
- Easy provider switching during chat
- Maintains chat history across provider switches
- Color-coded output for better readability
- Helpful error messages and command hints

## Testing

Run the test suite:
```bash
pytest test_llm_handler.py -v
```

The tests cover:
- API key validation
- Parameter handling
- Model selection
- System message functionality
- Error handling
- Provider-specific formatting

## Error Handling

The code includes comprehensive error handling for:
- Missing API keys
- Invalid API keys
- Network errors
- Provider-specific errors
- Invalid user input

Each error is caught and displayed with a helpful message and, where appropriate, suggestions for resolution.

## Dependencies

- openai: OpenAI API client
- anthropic: Anthropic API client
- termcolor: Colored terminal output
- pytest: Testing framework
- pytest-asyncio: Async support for pytest 