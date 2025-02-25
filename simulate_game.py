import requests
import json
from termcolor import cprint
import asyncio
import time
import sys
import os

# Initial board state
INITIAL_BOARD = """
Current turn: BLUE

8 RR BR GR GN RB BB GB RN 
7 RP BP GP GQ RQ BQ GK RK 
6 ·  ·  ·  ·  ·  ·  ·  ·  
5 ·  ·  ·  ·  ·  ·  ·  ·  
4 ·  ·  ·  ·  ·  ·  ·  ·  
3 ·  ·  ·  ·  ·  ·  ·  ·  
2 BP RP GP GN RN BN GB RB 
1 BR BP GR GQ RQ BQ GK RK 
  a  b  c  d  e  f  g  h 
"""

# LLM configurations for each player
PLAYERS = {
    "BLUE": {"provider": "openai", "model": "gpt-4o"},
    "GREEN": {"provider": "anthropic", "model": "claude-3-5-sonnet-latest"},
    "RED": {"provider": "openrouter", "model": "google/gemini-flash-1.5-8b"}
}

# Simple board representation for simulation
class SimpleBoard:
    def __init__(self, board_str):
        self.board_str = board_str
        self.turn = self._extract_turn()
        self.move_count = 0
        
    def _extract_turn(self):
        # Extract the current turn from the board string
        for line in self.board_str.split('\n'):
            if "Current turn:" in line:
                return line.split(":")[1].strip()
        return "BLUE"  # Default
    
    def make_move(self, start_pos, end_pos):
        # This is a very simplified simulation - in reality we'd update the actual board
        self.move_count += 1
        
        # Rotate turns: BLUE -> GREEN -> RED -> BLUE
        if self.turn == "BLUE":
            self.turn = "GREEN"
        elif self.turn == "GREEN":
            self.turn = "RED"
        else:
            self.turn = "BLUE"
            
        # Update the board string with the new turn
        lines = self.board_str.split('\n')
        for i, line in enumerate(lines):
            if "Current turn:" in line:
                lines[i] = f"Current turn: {self.turn}"
                break
        
        self.board_str = '\n'.join(lines)
        
        return self.board_str

async def get_move_from_llm(board, color, api_url="http://localhost:8000/get_move"):
    cprint(f"\n[{color} TURN] Getting move from {PLAYERS[color]['provider']}-{PLAYERS[color]['model']}...", "blue")
    
    # Prepare request data
    data = {
        "board_state": board.board_str,
        "color": color.lower(),
        "model_provider": PLAYERS[color]["provider"],
        "model_name": PLAYERS[color]["model"]
    }
    
    try:
        # Send request to server
        response = requests.post(api_url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            start_pos = result["start_position"]
            end_pos = result["end_position"]
            reasoning = result["reasoning"]
            
            cprint(f"[{color}] Move: {start_pos} → {end_pos}", "green")
            cprint(f"[{color}] Reasoning: {reasoning}", "cyan")
            
            return start_pos, end_pos, reasoning
        else:
            cprint(f"Error: HTTP {response.status_code}", "red")
            cprint(f"Response: {response.text}", "red")
            return None, None, None
            
    except Exception as e:
        cprint(f"Error connecting to server: {str(e)}", "red")
        return None, None, None

async def simulate_game(num_rounds=3):
    cprint("=== ThreeChess LLM Game Simulation ===", "blue", attrs=["bold"])
    cprint("Starting a new game with the following players:", "yellow")
    
    for color, config in PLAYERS.items():
        cprint(f"{color}: {config['provider']}-{config['model']}", "yellow")
    
    # Initialize the board
    board = SimpleBoard(INITIAL_BOARD)
    
    # Play rounds
    for round_num in range(1, num_rounds + 1):
        cprint(f"\n=== ROUND {round_num} ===", "magenta", attrs=["bold"])
        
        # Each player makes a move
        for _ in range(3):  # 3 players
            color = board.turn
            cprint(f"\nCurrent board state:", "white")
            cprint(board.board_str, "white")
            
            # Get move from LLM
            start_pos, end_pos, reasoning = await get_move_from_llm(board, color)
            
            if start_pos and end_pos:
                # Update board with the move
                board.make_move(start_pos, end_pos)
                time.sleep(1)  # Small delay between moves
            else:
                cprint(f"Failed to get a valid move for {color}. Skipping turn.", "red")
                board.turn = "GREEN" if color == "BLUE" else ("RED" if color == "GREEN" else "BLUE")
    
    cprint("\n=== Game Simulation Complete ===", "blue", attrs=["bold"])
    cprint(f"Total moves: {board.move_count}", "yellow")

if __name__ == "__main__":
    asyncio.run(simulate_game(num_rounds=2)) 