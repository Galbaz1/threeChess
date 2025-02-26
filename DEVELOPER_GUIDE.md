# ThreeChess Developer Guide

This guide provides instructions for developers working on the ThreeChess codebase. Follow these guidelines to ensure changes are made safely without compromising core game mechanics.

## Project Goal: LLM Test Arena

The goal is to transform ThreeChess into a modern LLM test arena where:
1. Three unique AI agents compete against each other
2. Users can select different LLM models for each agent via OpenRouter, see examples in @call_all
3. Core game mechanics remain intact

## Core Game Logic Files

These files define the fundamental game mechanics and should be modified with extreme caution:

- @src/threeChess/PieceType.java - Defines piece movement patterns
- @src/threeChess/Board.java - Implements move validation and game state
- @src/threeChess/Position.java - Handles board coordinates and position calculations
- @src/threeChess/Direction.java - Defines basic movement directions

## Implementation Steps

### Step 1: Setup OpenRouter Integration

1. Create a new package @src/threeChess/llm/ for LLM integration
2. Implement OpenRouter client using their API:

```java
// Create OpenRouter client utility
package threeChess.llm;

import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
// Additional imports

public class OpenRouterClient {
    private static final String API_BASE_URL = "https://openrouter.ai/api/v1";
    private final String apiKey;
    
    public OpenRouterClient() {
        // Use system variables for API keys
        this.apiKey = System.getenv("OPENROUTER_API_KEY");
        if (this.apiKey == null) {
            System.err.println("Error: OPENROUTER_API_KEY environment variable not set");
            // Handle error appropriately
        }
    }
    
    // Methods for model inference
}
```
Or else use the Python Openrouter setup, your choice.

### Step 2: Create LLM Agent Interface

Build an adapter between LLM responses and the Agent interface:

```java
// Create LLM-based agent
package threeChess.agents;

import threeChess.Agent;
import threeChess.Board;
import threeChess.Colour;
import threeChess.Position;
import threeChess.llm.OpenRouterClient;

public class LLMAgent extends Agent {
    private final String modelName;
    private final OpenRouterClient client;
    
    public LLMAgent(String modelName) {
        this.modelName = modelName;
        this.client = new OpenRouterClient();
        System.out.println("Created LLM agent using model: " + modelName);
    }
    
    @Override
    public Position[] makeMove(Board board, Colour colour) {
        try {
            // 1. Convert board state to prompt
            // 2. Send to LLM via OpenRouter
            // 3. Parse response into a valid move
            // 4. Return the move
        } catch (Exception e) {
            System.err.println("Error with LLM agent: " + e.getMessage());
            // Fallback move logic
        }
    }
}
```

### Step 3: Create Model Selection UI

Add model selection capabilities to the game interface:

1. Modify @ThreeChessDisplay.java to include model selection
2. Create a models configuration file

### Step 4: Implement Prompt Engineering

Create effective prompts that explain the game state and rules to the LLM:

1. Board state representation
2. Available moves
3. Game history
4. Strategic considerations

### Step 5: Add Response Parsing

Implement robust parsing of LLM responses into valid moves:

1. Validate LLM outputs
2. Handle edge cases and errors
3. Implement fallback strategies

## OpenRouter Integration Details

Use the OpenRouter API as follows:

```java
// Example OpenRouter API call
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create(API_BASE_URL + "/chat/completions"))
    .header("Content-Type", "application/json")
    .header("Authorization", "Bearer " + apiKey)
    .header("HTTP-Referer", "https://yourwebsite.com")  // Optional for rankings
    .header("X-Title", "ThreeChess LLM Arena")          // Optional for rankings
    .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
    .build();

HttpResponse<String> response = HttpClient.newHttpClient()
    .send(request, HttpResponse.BodyHandlers.ofString());
```

### Model Selection

Let users choose from available models for each player:

1. Create a dropdown in the UI for each player color
2. Populate with models from OpenRouter
3. Store user selections and create appropriate agents

## Common Tasks and Code References

### 1. Modifying Piece Movement Rules

**DO NOT MODIFY** unless absolutely necessary. Any changes risk breaking core game mechanics.

Reference:
- @src/threeChess/PieceType.java:getSteps() - Movement patterns for each piece
- @src/threeChess/PieceType.java:getStepReps() - How many steps a piece can take

Example of critical code that defines piece movements:
```java
// Pawn movement definition
private static Direction[][] pawnSteps(){
  return new Direction[][] {
    {Direction.FORWARD},
    {Direction.FORWARD,Direction.FORWARD},
    {Direction.FORWARD,Direction.LEFT},
    {Direction.LEFT,Direction.FORWARD},
    {Direction.FORWARD,Direction.RIGHT},
    {Direction.RIGHT,Direction.FORWARD}
  };
}
```

### 2. Implementing New AI Agents

The safest way to extend the game is by creating new AI agents:

1. Create a new file in `src/threeChess/agents/` 
2. Extend the `Agent` class
3. Implement the `makeMove(Board board, Colour colour)` method

Reference:
- `@src/threeChess/Agent.java` - Base class for all agents
- `@src/threeChess/agents/*.java` - Example agents

### 3. Modifying the UI

UI changes should be made in the display class:

Reference:
- `@src/threeChess/ThreeChessDisplay.java` - Handles all UI rendering

Be careful when modifying UI elements that interact with the board state.

### 4. Working with Board State

When accessing board state:

Reference:
- `@src/threeChess/Board.java:getPositions()` - Get positions of pieces
- `@src/threeChess/Board.java:getPiece()` - Get piece at position
- `@src/threeChess/Board.java:isLegalMove()` - Check if a move is legal

### 5. Adding Game Features

New game features should be added without modifying core mechanics:

- Add new scoring methods in a separate class
- Implement tournament structures in `ThreeChess.java`
- Add time control features by extending existing methods

## Safe and Unsafe Modifications

### Safe to Modify:
- ✅ AI agent implementations (`src/threeChess/agents/*`)
- ✅ UI appearance and rendering (`ThreeChessDisplay.java`)
- ✅ Tournament structure and game setup (`ThreeChess.java`)
- ✅ Adding debug/logging features
- ✅ LLM integration and OpenRouter client (`src/threeChess/llm/*`)

### Requires Caution:
- ⚠️ Board state representation (`Board.java`)
- ⚠️ Move history tracking
- ⚠️ Time control mechanisms
- ⚠️ Board-to-prompt conversion

### Unsafe to Modify:
- ❌ Piece movement patterns (`PieceType.getSteps()`)
- ❌ Direction definitions (`Direction.java`)
- ❌ Position calculations (`Position.java`)
- ❌ Legal move validation logic (`Board.isLegalMove()`)

## Testing After Changes

After any modifications:

1. Run a full game between basic agents to ensure core mechanics work
2. Verify all special moves (castling, pawn promotion)
3. Check that the win condition (king capture) works properly
4. Test LLM integration with various models
5. Validate error handling when API calls fail

## Bug Fixes and Pull Requests

When submitting bug fixes:
1. Document which files are being changed
2. Explain why the change is necessary
3. If modifying core game logic, provide extensive test cases
4. Get approval from at least one other developer

## Questions and Support

For questions about safe implementation practices, contact the project maintainers before making potentially breaking changes.

## Dependencies

Add the following to your `requirements.txt`:
```
java-http-client
json
``` 