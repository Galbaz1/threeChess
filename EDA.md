# ThreeChess Exploratory Data Analysis

## Project Overview

ThreeChess is a three-player chess variant played on a special board between Blue, Green, and Red players. This document tracks our findings and analysis as we develop an LLM-based agent to play this game.

## Game Mechanics

### Unique Aspects of Three-Player Chess

1. **Player Dynamics**: Unlike traditional chess with a clear opponent, in three-player chess, alliances can form and shift throughout the game.

2. **Board Structure**: The board is divided into three color-coded regions, one for each player.

3. **Victory Conditions**: The game ends when one player captures another player's king. The captor is the winner, the player who lost their king is the loser, and the third player neither wins nor loses.

4. **Move Priority**: Blue always moves first, followed by Green, and then Red.

## Initial Observations

### LLM Agent Development Challenges

1. **State Representation**: Representing the three-player board state in a way that an LLM can understand and reason about.

2. **Strategic Complexity**: The LLM needs to understand not just piece values and positions, but also the complex dynamics between three players.

3. **API Integration**: Building a bridge between the Java-based game engine and the Python-based LLM API service.

### Game Strategy Considerations

1. **Balance of Power**: The LLM agent should be able to assess when to attack and when to defend based on the relative strengths of all three players.

2. **Temporary Alliances**: Sometimes it's beneficial to avoid attacking a weaker player to prevent the third player from gaining an advantage.

3. **Center Control**: Controlling the center of the board remains important, but the definition of "center" is different in a three-player layout.

## Next Steps

1. **Game Data Collection**: Run multiple games with the LLM agent against random opponents to collect performance data.

2. **Prompt Refinement**: Iteratively improve the LLM system prompt based on observed play patterns and weaknesses.

3. **Strategic Analysis**: Analyze successful and unsuccessful games to identify key decision points and strategic patterns.

## LLM Performance Metrics

We will track the following metrics as we collect data:

1. Win/Loss ratio
2. Average game length
3. Frequency of tactical patterns
4. Quality of move explanations

_This document will be updated as new insights are discovered through gameplay and analysis._ 