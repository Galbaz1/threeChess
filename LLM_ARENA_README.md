# ThreeChess LLM Arena

A modern application for testing different LLM models against each other in a three-player chess game.

## Overview

ThreeChess LLM Arena allows you to pit different LLM models (OpenAI, Anthropic, OpenRouter, Groq) against each other in a three-player chess game. Each player (Blue, Green, Red) can be controlled by a different LLM model, allowing you to compare their strategic thinking and decision-making abilities.

## Architecture

The application consists of three main components:

1. **Python FastAPI Server (llm_server.py)**: Handles LLM API calls and move generation
2. **Flask Web Application (web_app.py)**: Provides a user-friendly web interface
3. **Game Simulation (simulate_game.py)**: Handles the game logic and board state

## Requirements

### Python Dependencies
- FastAPI
- Uvicorn
- Pydantic
- Termcolor
- OpenAI
- Anthropic
- Requests
- Flask
- PyGame
- Jinja2

### Java Dependencies
- Java 8 or higher
- JSON Simple library (for Java implementation)

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables for API keys:
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   export OPENROUTER_API_KEY="your-openrouter-key"
   export GROQ_API_KEY="your-groq-key"
   ```

## Running the Application

### Option 1: Using the Start Script (Recommended)

The easiest way to start the application is to use the provided start script:

```bash
python start_threechess.py
```

This will start both the LLM server and web application, and automatically open your browser to the web interface.

### Option 2: Starting Servers Individually

#### Start the Python LLM Server

```bash
python llm_server.py
```

This will start the FastAPI server on port 8000.

#### Start the Web Application

```bash
python web_app.py
```

This will start the Flask web application on port 5050. Open your browser and navigate to:

```
http://localhost:5050
```

## Using the Web Interface

1. **Configure Players**: Select the LLM provider and model for each player (Blue, Green, Red)
2. **Start Game**: Click the "Start Game" button to begin the game
3. **Make Move**: Click the "Make Move" button to manually trigger a move (or let the automatic mode run)
4. **Reset Game**: Click the "Reset Game" button to reset the game to the initial state

## Testing

You can test the servers with:

```bash
python test_web_app.py
```

This will check if both the LLM server and web application are running correctly.

## How It Works

1. The web interface allows you to configure which LLM models to use for each player
2. When a move is requested, the web app sends the current board state to the LLM server
3. The LLM server formats an appropriate prompt for the selected LLM
4. The LLM analyzes the board and suggests a move
5. The server parses the response and returns a valid move
6. The web app updates the board and displays the move

## Customizing Models

You can customize which models to use through the web interface, or by modifying the `PLAYERS` dictionary in `simulate_game.py`:

```python
PLAYERS = {
    "BLUE": {"provider": "openai", "model": "gpt-4o"},
    "GREEN": {"provider": "anthropic", "model": "claude-3-5-sonnet-latest"},
    "RED": {"provider": "openrouter", "model": "google/gemini-flash-1.5-8b"}
}
```

## Future Improvements

1. Add proper move validation in the Python simulation
2. Implement actual piece movement on the board visualization
3. Add game history tracking and analysis
4. Implement tournament mode to compare multiple models
5. Add support for more LLM providers 