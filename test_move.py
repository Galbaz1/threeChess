import asyncio
import requests
from termcolor import cprint
import json
import sys
import os

# Import our game logic
from simulate_game import SimpleBoard, get_move_from_llm, INITIAL_BOARD, PLAYERS

async def test_single_move():
    """Test a single move through the LLM server"""
    cprint("=== Testing ThreeChess LLM Move ===", "blue", attrs=["bold"])
    
    # Initialize a board
    board = SimpleBoard(INITIAL_BOARD)
    color = board.turn  # Should be BLUE
    
    cprint(f"Current board state:", "white")
    cprint(board.board_str, "white")
    cprint(f"Current turn: {color}", "cyan")
    
    # Get move from LLM
    cprint(f"\nRequesting move from LLM server...", "yellow")
    try:
        start_pos, end_pos, reasoning = await get_move_from_llm(board, color)
        
        if start_pos and end_pos:
            cprint(f"Success! Received move:", "green")
            cprint(f"Start position: {start_pos}", "green")
            cprint(f"End position: {end_pos}", "green")
            cprint(f"Reasoning: {reasoning}", "green")
            
            # Update board with the move
            board.make_move(start_pos, end_pos)
            cprint(f"\nUpdated board state:", "white")
            cprint(board.board_str, "white")
            cprint(f"Next turn: {board.turn}", "cyan")
            
            return True
        else:
            cprint("Failed to get a valid move from the LLM server.", "red")
            return False
    except Exception as e:
        cprint(f"Error during test: {str(e)}", "red")
        return False

if __name__ == "__main__":
    cprint("ThreeChess LLM Move Test", "blue", attrs=["bold"])
    
    # Run the test
    success = asyncio.run(test_single_move())
    
    if success:
        cprint("\nTest completed successfully!", "green", attrs=["bold"])
        sys.exit(0)
    else:
        cprint("\nTest failed!", "red", attrs=["bold"])
        sys.exit(1) 