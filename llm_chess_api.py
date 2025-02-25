#!/usr/bin/env python3
from flask import Flask, request, jsonify
from openai import AsyncOpenAI
import os
import json
import asyncio
from termcolor import colored
import sys
import time
import re
import traceback
from datetime import datetime
from langsmith import traceable
from langsmith_helper import LangSmithHelper

# CONSTANTS
PORT = 5002
MODEL = "o3-mini"  # switch to o3-mini
MAX_TOKENS = 5000
REASONING_EFFORT = "medium"  # Changed from "low" to "medium" for better tool usage
VALID_FILES = ['A', 'B', 'C']
VALID_RANKS = ['1', '2', '3', '4']
VALID_COLORS = ['R', 'B', 'G']

# Initialize LangSmith helper
LANGSMITH_API_KEY = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
langsmith_helper = LangSmithHelper(
    api_key=LANGSMITH_API_KEY,
    project=os.getenv("LANGCHAIN_PROJECT") or os.getenv("LANGSMITH_PROJECT", "chess"),
    tracing_enabled=os.getenv("LANGCHAIN_TRACING_V2") == "true" or os.getenv("LANGSMITH_TRACING") == "true"
)

# Global tracking for agent memory
AGENT_MEMORY = {
    "moves": [],
    "token_usage": [],
    "thinking_stats": [],
    "game_state_history": [],
    "start_time": None,
    "debug_info": []  # Added to store more detailed debugging information
}

app = Flask(__name__)

# Initialize OpenAI client with LangSmith wrapping
langsmith_helper.initialize()
client = langsmith_helper.get_async_client()

# Function to validate ThreeChess positions
def is_valid_position(pos_str):
    """Validate if a position string follows the ThreeChess coordinate system"""
    try:
        if not pos_str or len(pos_str) != 3:
            print(colored(f"Invalid position format: {pos_str} - must be 3 characters", "red"))
            return False
            
        color, file, rank = pos_str[0], pos_str[1], pos_str[2]
        
        if color not in VALID_COLORS:
            print(colored(f"Invalid color in position {pos_str}: {color} - must be R, B, or G", "red"))
            return False
            
        if file not in VALID_FILES:
            print(colored(f"Invalid file in position {pos_str}: {file} - must be A, B, or C", "red"))
            return False
            
        if rank not in VALID_RANKS:
            print(colored(f"Invalid rank in position {pos_str}: {rank} - must be 1, 2, 3, or 4", "red"))
            return False
            
        return True
    except Exception as e:
        print(colored(f"Error validating position: {str(e)}", "red"))
        return False

def validate_and_process_move(move_str, legal_moves=None):
    """Validate and process a move string against legal moves"""
    try:
        # Clean up the move string
        move_str = move_str.strip()
        positions = move_str.split()
        
        if len(positions) != 2:
            print(colored(f"Invalid move format: {move_str} - must contain exactly two positions", "red"))
            return None
            
        from_pos, to_pos = positions
        
        # Validate both positions
        if not is_valid_position(from_pos) or not is_valid_position(to_pos):
            print(colored(f"Invalid position in move: {move_str}", "red"))
            return None
            
        # Check if move is in legal moves (if provided)
        if legal_moves and move_str not in legal_moves:
            print(colored(f"Move {move_str} is not in the list of legal moves", "yellow"))
            # Find closest legal move for debugging
            closest_move = find_closest_legal_move(move_str, legal_moves)
            if closest_move:
                print(colored(f"Did you mean: {closest_move}?", "yellow"))
            return None
            
        return move_str
    except Exception as e:
        print(colored(f"Error processing move: {str(e)}", "red"))
        return None
        
def find_closest_legal_move(move_str, legal_moves):
    """Find the closest legal move to the provided move"""
    try:
        # Simple implementation - find moves from the same position
        if not move_str or not legal_moves:
            return None
            
        parts = move_str.split()
        if not parts or len(parts) < 1:
            return legal_moves[0] if legal_moves else None
            
        from_pos = parts[0]
        closest = [move for move in legal_moves if move.startswith(from_pos)]
        return closest[0] if closest else legal_moves[0]
    except:
        return legal_moves[0] if legal_moves else None

# Unicode symbols for chess pieces
PIECE_SYMBOLS = {
    'BLUE': {
        'KING': '♔',
        'QUEEN': '♕',
        'ROOK': '♖',
        'BISHOP': '♗',
        'KNIGHT': '♘',
        'PAWN': '♙'
    },
    'RED': {
        'KING': '♚',
        'QUEEN': '♛',
        'ROOK': '♜',
        'BISHOP': '♝',
        'KNIGHT': '♞',
        'PAWN': '♟'
    },
    'GREEN': {
        'KING': '♔',
        'QUEEN': '♕',
        'ROOK': '♖',
        'BISHOP': '♗',
        'KNIGHT': '♘',
        'PAWN': '♙'
    }
}

# Color mapping for terminal output
COLOR_MAP = {
    'BLUE': 'blue',
    'RED': 'red',
    'GREEN': 'green'
}

def format_board_unicode(board_state):
    """
    Format the board state into a Unicode representation with named fields and piece placement.
    
    Args:
        board_state (str): The raw board state from the Java application
    
    Returns:
        str: A Unicode representation of the 3-player chess board
    """
    try:
        print(colored("Formatting board to Unicode representation...", "cyan"))
        
        # Parse the raw board state to extract piece positions
        pieces = {}
        current_color = None
        current_turn = None
        captured_pieces = {}
        parsing_captured = False
        time_remaining = {}
        
        for line in board_state.split('\n'):
            if line.startswith("Current turn:"):
                current_turn = line.split(":")[1].strip()
            elif "Captured pieces:" in line:
                parsing_captured = True
                continue
            elif parsing_captured and line.strip():
                if ":" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        color = parts[0].split()[0].strip()
                        pieces_str = parts[1].strip()
                        captured_pieces[color] = pieces_str
            elif "time:" in line:
                # Extract time information
                parts = line.split("time:")
                if len(parts) >= 2:
                    color = parts[0].strip()
                    time_ms = parts[1].split()[0].strip()
                    try:
                        time_remaining[color] = int(time_ms)
                    except ValueError:
                        pass
            elif "pieces:" in line:
                parsing_captured = False
                current_color = line.split(" ")[0].strip()
            elif ":" in line and current_color and not parsing_captured:
                parts = line.split(":")
                if len(parts) == 2:
                    position = parts[0].strip()
                    piece_type = parts[1].strip()
                    pieces[position] = (current_color, piece_type)
        
        # Create the Unicode board representation
        board_unicode = []
        board_unicode.append("Three-Player Chess Board (Unicode Representation)")
        board_unicode.append("Current Turn: " + colored(current_turn, COLOR_MAP.get(current_turn, 'white')))
        
        # Add time information if available
        if time_remaining:
            board_unicode.append("\nTime Remaining:")
            for color in ['BLUE', 'RED', 'GREEN']:
                if color in time_remaining:
                    time_sec = time_remaining[color] / 1000.0
                    board_unicode.append(colored(f"  {color}: {time_sec:.1f} seconds", COLOR_MAP.get(color, 'white')))
        
        board_unicode.append("")
        
        # Add legend for piece symbols
        board_unicode.append("Legend:")
        for color in ['BLUE', 'RED', 'GREEN']:
            color_line = colored(f"{color}: ", COLOR_MAP.get(color, 'white'))
            for piece_type, symbol in PIECE_SYMBOLS[color].items():
                color_line += f"{symbol}={piece_type} "
            board_unicode.append(color_line)
        board_unicode.append("")
        
        # Add a coordinate system explanation
        board_unicode.append("Coordinate System:")
        board_unicode.append("- Each position is marked as {COLOR}{FILE}{RANK}")
        board_unicode.append("- Example: " + 
            colored("B", "blue") + "A1 = Blue's A1, " + 
            colored("R", "red") + "C3 = Red's C3, " + 
            colored("G", "green") + "E2 = Green's E2")
        board_unicode.append("")
        
        # Create a board with actual pieces placed on it
        # First create empty board template
        blue_section = []
        red_section = []
        green_section = []
        
        # Create the board template for each section
        for rank in range(1, 5):  # Ranks 1-4
            blue_rank = []
            for file in range(8):  # Files A-H
                file_letter = chr(65 + file)  # A-H
                pos = f"B{file_letter}{rank}"
                blue_rank.append(pos)
            blue_section.append(blue_rank)
            
        for rank in range(1, 5):  # Ranks 1-4
            red_rank = []
            for file in range(8):  # Files A-H
                file_letter = chr(65 + file)  # A-H
                pos = f"R{file_letter}{rank}"
                red_rank.append(pos)
            red_section.append(red_rank)
            
        for rank in range(1, 5):  # Ranks 1-4
            green_rank = []
            for file in range(8):  # Files A-H
                file_letter = chr(65 + file)  # A-H
                pos = f"G{file_letter}{rank}"
                green_rank.append(pos)
            green_section.append(green_rank)
        
        # Create a visual board with pieces
        visual_board = [
            "                  " + colored("BLUE SECTION", "blue"),
            "                  A   B   C   D   E   F   G   H"
        ]
        
        # Add Blue section (reversed to show from bottom to top)
        for rank, row in enumerate(blue_section):
            rank_num = rank + 1
            board_row = f"               {rank_num}  "
            for pos in row:
                if pos in pieces:
                    color, piece_type = pieces[pos]
                    piece_symbol = PIECE_SYMBOLS[color].get(piece_type, '·')
                    piece_display = colored(piece_symbol, COLOR_MAP.get(color, 'white'))
                else:
                    piece_display = '·'
                board_row += piece_display + "   "
            visual_board.append(colored(board_row, "blue"))
        
        # Add middle separator with coordinate labels
        middle_row = colored("RED", "red") + " H G F E D C B A " + "| | | | | | | |" + " A B C D E F G H " + colored("GREEN", "green")
        visual_board.append(middle_row)
        
        # Create rows with both Red and Green sections
        for rank in range(4):
            rank_num = 4 - rank
            red_row = f"{' ' * (8 - rank_num)}  {rank_num} "
            for pos in reversed(red_section[rank_num-1]):
                if pos in pieces:
                    color, piece_type = pieces[pos]
                    piece_symbol = PIECE_SYMBOLS[color].get(piece_type, '·')
                    piece_display = colored(piece_symbol, COLOR_MAP.get(color, 'white'))
                else:
                    piece_display = '·'
                red_row += piece_display + " "
            
            separator = "   "
            
            green_row = ""
            for pos in green_section[rank_num-1]:
                if pos in pieces:
                    color, piece_type = pieces[pos]
                    piece_symbol = PIECE_SYMBOLS[color].get(piece_type, '·')
                    piece_display = colored(piece_symbol, COLOR_MAP.get(color, 'white'))
                else:
                    piece_display = '·'
                green_row += piece_display + " "
            
            full_row = red_row + separator + green_row
            visual_board.append(full_row)
        
        # Add the visual board to the output
        board_unicode.append("Board Layout (pieces shown):")
        board_unicode.extend(visual_board)
        board_unicode.append("")
        
        # Still include the detailed piece list for reference
        board_unicode.append("Current Pieces on Board:")
        
        # Organize pieces by color sections
        sections = {'BLUE': [], 'RED': [], 'GREEN': []}
        
        # Group pieces by their section
        for pos, (color, piece_type) in pieces.items():
            piece_symbol = PIECE_SYMBOLS[color].get(piece_type, '?')
            colored_pos = colored(pos[0], COLOR_MAP.get(color, 'white')) + pos[1:]
            sections[color].append(f"{colored_pos}: {piece_symbol} ({piece_type})")
        
        # Display pieces by section
        for color in ['BLUE', 'RED', 'GREEN']:
            section_pieces = sections[color]
            if section_pieces:
                header = colored(f"{color} SECTION PIECES:", COLOR_MAP.get(color, 'white'))
                board_unicode.append(header)
                
                # Display in rows of 4 pieces
                for i in range(0, len(section_pieces), 4):
                    row = section_pieces[i:i+4]
                    board_unicode.append("  " + "  ".join(row))
                
                board_unicode.append("")
        
        # Add captured pieces information
        if captured_pieces:
            board_unicode.append("Captured Pieces:")
            for color in ['BLUE', 'RED', 'GREEN']:
                if color in captured_pieces:
                    captured = captured_pieces[color]
                    board_unicode.append(colored(f"  {color} captured: {captured}", COLOR_MAP.get(color, 'white')))
            board_unicode.append("")
        
        return "\n".join(board_unicode)
    except Exception as e:
        print(colored(f"Error formatting Unicode board: {e}", "red"))
        # Print the stack trace for debugging
        traceback.print_exc()
        return "Error creating Unicode board representation"

@traceable(name="ThreeChess_GetLLMMove", run_type="llm")
async def get_llm_move(board_state, current_color, error_feedback=None):
    """
    Query the LLM to get the best move based on the current board state.
    """
    print(colored(f"Getting move for {current_color}...", "cyan"))
    print(colored("Analyzing board state...", "cyan"))
    
    # Initialize game start time if this is the first move
    if AGENT_MEMORY["start_time"] is None:
        AGENT_MEMORY["start_time"] = datetime.now().isoformat()
    
    # Create a timestamp for this move request
    timestamp = datetime.now().isoformat()
    
    try:
        # Parse time information from board_state
        time_remaining = {}
        time_info = {"current_player_time": None, "avg_time_per_move": None}
        
        for line in board_state.split('\n'):
            if "time:" in line:
                parts = line.split("time:")
                if len(parts) >= 2:
                    color = parts[0].strip()
                    time_ms = parts[1].split()[0].strip()
                    try:
                        time_remaining[color] = int(time_ms)
                        # Track the current player's time
                        if color == current_color:
                            time_info["current_player_time"] = int(time_ms) / 1000.0  # Convert to seconds
                    except ValueError:
                        pass
        
        # Calculate average time per move based on previous moves
        player_moves = [m for m in AGENT_MEMORY["moves"] if m["color"] == current_color]
        if player_moves:
            total_thinking_time = sum(m["thinking_time"] for m in player_moves)
            time_info["avg_time_per_move"] = total_thinking_time / len(player_moves)
            print(colored(f"Average time per move: {time_info['avg_time_per_move']:.2f} seconds", "magenta"))
        
        # Create a Unicode representation of the board
        unicode_board = format_board_unicode(board_state)
        
        # Prepare the system message with chess rules and strategy considerations
        system_message = """
        You are an expert three-player chess AI. You're analyzing a game with Blue, Green, and Red players.
        
        Three-Player Chess Rules:
        1. The game is played on a special hexagonal board with three color-coded sections.
        2. Each player has standard chess pieces (King, Queen, Rook, Bishop, Knight, Pawn).
        3. Players take turns moving clockwise (Blue, then Green, then Red).
        4. A player loses when their King is captured (not checkmate).
        5. When a player is eliminated, their pieces remain on the board but can't move.
        6. The last player with a King wins.
        
        Piece Movement Rules:
        - KING moves one square in any direction.
        - QUEEN moves any number of squares along a rank, file, or diagonal.
        - ROOK moves any number of squares horizontally or vertically.
        - BISHOP moves any number of squares diagonally.
        - KNIGHT moves in an 'L' shape: two squares in one direction and then one perpendicular.
        - PAWN moves forward one square (or two on its first move) and captures diagonally.
        
        Things You Cannot Do:
        1. You cannot move to a square occupied by your own piece.
        2. You cannot move through other pieces (except Knights).
        3. You cannot make a move that leaves your King in check.
        4. You cannot capture your own pieces.
        
        TIME CONSTRAINTS:
        - You have a limited amount of time to make all your moves.
        - If you exceed your time allocation, you will lose points.
        - Make your moves quickly when the position is clear.
        - Consider the time remaining when planning complex moves.
        
        COORDINATE SYSTEM (VERY IMPORTANT):
        - Each position on the board is identified by {COLOR}{FILE}{RANK}
        - COLOR is the section color prefix (B=Blue, R=Red, G=Green)
        - FILE is the column (A, B, or C only)
        - RANK is the row (1, 2, 3, or 4 only)
        - EXAMPLES:
          * BA1 = Blue's A1 square (Blue section, A file, 1 rank)
          * RB2 = Red's B2 square (Red section, B file, 2 rank)
          * GC3 = Green's C3 square (Green section, C file, 3 rank)
        - All coordinates MUST include the color prefix (B, R, or G)
        - Each player's coordinates are oriented from their perspective
        - CRITICAL: Only files A-C and ranks 1-4 exist. Coordinates like RD5 or RF6 DO NOT EXIST.
        
        VALID MOVES FORMAT (CRITICAL):
        - A move consists of two position coordinates separated by a space
        - Format: "{COLOR}{FILE}{RANK} {COLOR}{FILE}{RANK}"
        - VALID EXAMPLES:
          * "BA2 BA4" (Blue's pawn from A2 to A4)
          * "RB1 RC3" (Red's knight from B1 to C3)
          * "GC2 GC4" (Green's pawn from C2 to C4)
        - INVALID EXAMPLES:
          * "A2 A4" (missing color prefix)
          * "BA2-BA4" (wrong separator, use space not dash)
          * "BA2 to BA4" (wrong format, no "to" between positions)
          * "RD5 RE7" (invalid: these positions don't exist, only A-C files and 1-4 ranks exist)
        
        You will use the think tool to analyze the position and explain your reasoning.
        Then you will use the decide_move tool to provide your final move decision.
        """
        
        # Define tools for the LLM to use
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "think",
                    "description": "Analyze the chess position and explain your reasoning before making a move.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis": {
                                "type": "string",
                                "description": "Your detailed analysis of the position, potential moves, threats, and strategy"
                            }
                        },
                        "required": ["analysis"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "decide_move",
                    "description": "Provide your final move decision in the required format.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "move": {
                                "type": "string", 
                                "description": "Your chess move in the format '{COLOR}{FILE}{RANK} {COLOR}{FILE}{RANK}' (e.g., 'RC2 RC4', 'GB1 GC3', 'BA2 BA3') - only positions with files A-C and ranks 1-4 exist"
                            }
                        },
                        "required": ["move"]
                    }
                }
            }
        ]
        
        # Add time information to the user message
        time_message = ""
        if time_info["current_player_time"] is not None:
            time_message = f"\nTIME INFORMATION:\n- Your remaining time: {time_info['current_player_time']:.1f} seconds"
            
            if time_info["avg_time_per_move"] is not None:
                time_message += f"\n- Your average time per move: {time_info['avg_time_per_move']:.1f} seconds"
                
                # Add time management advice
                if time_info["current_player_time"] < 30:
                    time_message += "\n- WARNING: Very low time remaining. Make a move quickly!"
                elif time_info["current_player_time"] < 60:
                    time_message += "\n- CAUTION: Low time remaining. Consider faster moves."
                elif time_info["avg_time_per_move"] * 10 > time_info["current_player_time"]:
                    time_message += "\n- NOTE: Time is becoming a concern. Consider efficient moves."
        
        # Prepare the user message with just the current game state
        user_message = f"""
        It is now your turn to move as {current_color}.
        {time_message}
        
        {unicode_board}
        """
        
        # Add error feedback if provided
        if error_feedback:
            print(colored(f"Including error feedback: {error_feedback}", "yellow"))
            user_message += f"""
        IMPORTANT ERROR - PLEASE FIX:
        {error_feedback}
        
        VALID MOVE FORMAT REMINDER:
        1. Your move must be in the format: {{COLOR}}{{FILE}}{{RANK}} {{COLOR}}{{FILE}}{{RANK}}
        2. Example: "BA2 BA3", "RB1 RC3", "GC2 GC3"
        3. The color prefix (B, R, or G) is REQUIRED for ALL coordinates
        4. There must be exactly ONE SPACE between coordinates
        5. CRITICAL: Only files A-C and ranks 1-4 exist. Coordinates like RD5 or RF6 are INVALID.
        
        For example, to move a piece:
        - RIGHT: BA2 BA3, RC2 RC3, GB1 GC3
        - WRONG: A2 A4 (missing color prefix)
        - WRONG: RD5 RE7 (these positions don't exist - only files A-C and ranks 1-4 exist)
        """
        
        print(colored(f"Sending request to {MODEL} with reasoning_effort={REASONING_EFFORT}...", "cyan"))
        
        start_time = time.time()
        
        # Make the OpenAI call with tools to extract reasoning
        response = await client.chat.completions.create(
            model=MODEL,
            reasoning_effort=REASONING_EFFORT,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            tools=tools,
            tool_choice="auto",
            max_completion_tokens=MAX_TOKENS
        )
        
        elapsed_time = time.time() - start_time
        
        # Extract and log token usage information
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens
        
        # Get reasoning tokens details if available
        reasoning_tokens = 0
        if hasattr(usage, 'completion_tokens_details') and usage.completion_tokens_details:
            if hasattr(usage.completion_tokens_details, 'reasoning_tokens'):
                reasoning_tokens = usage.completion_tokens_details.reasoning_tokens
        
        # Handle tool calls in the response
        reasoning_text = "No explicit reasoning provided"
        final_move = None
        
        if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                if function_name == "think":
                    reasoning_text = arguments.get("analysis", "No reasoning provided")
                    print(colored("\nAgent's Reasoning Process:", "yellow"))
                    print(colored("-----------------------", "yellow"))
                    print(colored(reasoning_text, "cyan"))
                    print(colored("-----------------------", "yellow"))
                
                if function_name == "decide_move":
                    move = arguments.get("move", "")
                    # Encapsulate the move with special tokens for easy extraction
                    final_move = f"<<MOVE>>{move}<<END_MOVE>>"
                    print(colored(f"\nFinal Move Decision: {move}", "green"))
        
        # If no tool calls or move not found, fall back to content
        if not final_move and response.choices[0].message.content:
            content = response.choices[0].message.content.strip()
            print(colored(f"Using content as fallback: {content}", "yellow"))
            
            # First look for the special move format in the content
            move_match = re.search(r'<<MOVE>>([^<]+)<<END_MOVE>>', content)
            if move_match:
                final_move = move_match.group(1).strip()
                print(colored(f"Extracted move from special format: {final_move}", "green"))
            else:
                # Try to extract reasoning from content if no tool call was made
                if reasoning_text == "No explicit reasoning provided":
                    # Look for patterns like "Reasoning:" or "Analysis:" in the content
                    reasoning_markers = ["reasoning:", "analysis:", "thinking:", "i think:"]
                    lower_content = content.lower()
                    
                    for marker in reasoning_markers:
                        if marker in lower_content:
                            parts = lower_content.split(marker, 1)
                            if len(parts) > 1:
                                # Extract everything after the marker until the next paragraph or move decision
                                reasoning_part = parts[1].strip()
                                move_markers = ["my move:", "move:", "i choose:", "final move:"]
                                
                                for move_marker in move_markers:
                                    if move_marker in reasoning_part.lower():
                                        reasoning_part = reasoning_part.split(move_marker, 1)[0].strip()
                                
                                reasoning_text = reasoning_part
                                print(colored("\nExtracted Reasoning from Content:", "yellow"))
                                print(colored("-----------------------", "yellow"))
                                print(colored(reasoning_text, "cyan"))
                                print(colored("-----------------------", "yellow"))
                                break
                
                # Try to extract the move from the content if not found through tools
                if not final_move:
                    # Look for common patterns indicating a move
                    move_markers = ["move:", "my move:", "i choose:", "final move:", "i play:"]
                    lower_content = content.lower()
                    
                    for marker in move_markers:
                        if marker in lower_content:
                            parts = lower_content.split(marker, 1)
                            if len(parts) > 1:
                                potential_move = parts[1].strip().split("\n")[0].strip()
                                # Clean up common formatting
                                potential_move = potential_move.replace(".", "").replace("'", "").replace("\"", "").strip()
                                
                                # Check if it looks like a valid move format (e.g., "RA1 RA3")
                                if " " in potential_move and len(potential_move) >= 5:
                                    final_move = potential_move
                                    print(colored(f"Extracted move from content: {final_move}", "green"))
                                    break
                    
                    # If still no move found, try to find something that looks like coordinates
                    if not final_move:
                        # Look for patterns like "RA1 to RA3" or "RA1-RA3" or "RA1→RA3"
                        move_patterns = [
                            r'([RGB][A-C][1-4])\s+to\s+([RGB][A-C][1-4])',
                            r'([RGB][A-C][1-4])\s*-\s*([RGB][A-C][1-4])',
                            r'([RGB][A-C][1-4])\s*→\s*([RGB][A-C][1-4])',
                            r'([RGB][A-C][1-4])\s+([RGB][A-C][1-4])'
                        ]
                        
                        for pattern in move_patterns:
                            matches = re.search(pattern, content)
                            if matches:
                                final_move = f"{matches.group(1)} {matches.group(2)}"
                                print(colored(f"Regex extracted move: {final_move}", "green"))
                                break
                
                # As a last resort, just use the content directly
                if not final_move:
                    # Remove common prefixes/explanations to try to get just the move
                    final_move = content
                    print(colored(f"Using full content as move (no structured move found): {final_move}", "yellow"))
                    
        # Check if we have a valid move decision
        if final_move is None or final_move == "":
            # The move extraction failed - let's look in the reasoning for a move
            print(colored("Move not found through tools, checking reasoning for a move...", "yellow"))
            
            # Look through the reasoning text for possible move patterns
            move_patterns = [
                r'([RGB][A-C][1-4])\s+to\s+([RGB][A-C][1-4])',
                r'([RGB][A-C][1-4])\s*-\s*([RGB][A-C][1-4])',
                r'([RGB][A-C][1-4])\s*→\s*([RGB][A-C][1-4])',
                r'([RGB][A-C][1-4])\s+([RGB][A-C][1-4])',
                r'moving\s+\w+\s+from\s+([RGB][A-C][1-4])\s+to\s+([RGB][A-C][1-4])',
                r'move\s+\w+\s+from\s+([RGB][A-C][1-4])\s+to\s+([RGB][A-C][1-4])',
                r'([RGB][A-C][1-4])[^\w]+([RGB][A-C][1-4])',
                r'from\s+([RGB][A-C][1-4])\s+to\s+([RGB][A-C][1-4])',
                r'play\s+([RGB][A-C][1-4])\s+to\s+([RGB][A-C][1-4])',
                r'([RGB])[^A-C\d]+([A-C][1-4])\s+to\s+([RGB])[^A-C\d]+([A-C][1-4])'  # Handles separate color mentions
            ]
            
            for pattern in move_patterns:
                matches = re.search(pattern, reasoning_text, re.IGNORECASE)
                if matches:
                    if len(matches.groups()) == 2:
                        final_move = f"{matches.group(1)} {matches.group(2)}"
                        print(colored(f"Extracted move from reasoning: {final_move}", "green"))
                        break
                    elif len(matches.groups()) == 4:  # Special case for separated color mentions
                        final_move = f"{matches.group(1)}{matches.group(2)} {matches.group(3)}{matches.group(4)}"
                        print(colored(f"Extracted move from reasoning with separated colors: {final_move}", "green"))
                        break
            
            # If still no move found, look for specific piece mentions that might indicate a move
            if final_move is None or final_move == "":
                # More comprehensive patterns to extract moves with piece references
                piece_patterns = [
                    r'knight\s+(?:on|at|from)?\s+([RGB][A-C][1-4])\s+(?:to|moves to|→)\s+([RGB][A-C][1-4])',
                    r'pawn\s+(?:on|at|from)?\s+([RGB][A-C][1-4])\s+(?:to|moves to|→)\s+([RGB][A-C][1-4])',
                    r'(?:king|queen|rook|bishop)\s+(?:on|at|from)?\s+([RGB][A-C][1-4])\s+(?:to|moves to|→)\s+([RGB][A-C][1-4])',
                    r'move\s+(?:the|my)?\s+\w+\s+(?:from)?\s+([RGB][A-C][1-4])\s+(?:to|towards)?\s+([RGB][A-C][1-4])',
                    r'([RGB][A-C][1-4])(?:\s+\w+){1,5}\s+([RGB][A-C][1-4])',  # More flexible pattern with words between
                    r'(?:on|at|from)\s+([RGB][A-C][1-4])(?:\s+\w+){1,3}\s+(?:to|towards)\s+([RGB][A-C][1-4])'
                ]
                
                for pattern in piece_patterns:
                    matches = re.search(pattern, reasoning_text, re.IGNORECASE)
                    if matches:
                        final_move = f"{matches.group(1)} {matches.group(2)}"
                        print(colored(f"Extracted move from piece reference: {final_move}", "green"))
                        break
                
                # Special handling for cases where the color prefix might be separate
                if final_move is None or final_move == "":
                    color_position_patterns = [
                        r'([RGB])\s*[^\w]*\s*([A-C][1-4])\s+(?:to|moves to|→)\s+([RGB])\s*[^\w]*\s*([A-C][1-4])',
                        r'from\s+([RGB])\s*[^\w]*\s*([A-C][1-4])\s+to\s+([RGB])\s*[^\w]*\s*([A-C][1-4])'
                    ]
                    
                    for pattern in color_position_patterns:
                        matches = re.search(pattern, reasoning_text, re.IGNORECASE)
                        if matches:
                            # Combine the separate color and position components
                            from_pos = f"{matches.group(1)}{matches.group(2)}"
                            to_pos = f"{matches.group(3)}{matches.group(4)}"
                            final_move = f"{from_pos} {to_pos}"
                            print(colored(f"Extracted move from separate color-position: {final_move}", "green"))
                            break
                
            # Additional extraction attempt - try to find any valid coordinates 
            # in close proximity as a last resort
            if final_move is None or final_move == "":
                coordinate_pattern = r'([RGB][A-C][1-4])'
                all_coordinates = re.findall(coordinate_pattern, reasoning_text)
                
                if len(all_coordinates) >= 2:
                    # Look for two coordinates that could form a valid move
                    for i in range(len(all_coordinates) - 1):
                        # Check if they're the same color (likely to be a valid move)
                        if all_coordinates[i][0] == all_coordinates[i+1][0]:
                            final_move = f"{all_coordinates[i]} {all_coordinates[i+1]}"
                            print(colored(f"Extracted potential move from coordinate proximity: {final_move}", "yellow"))
                            break
            
            # Last resort - set a default move if we've failed to extract one
            if final_move is None or final_move == "":
                # This should be extremely rare, but provide a basic default move
                # as a fallback, such as the standard opening pawn move
                if current_color == "BLUE":
                    final_move = "BA2 BA3"
                elif current_color == "RED":
                    final_move = "RA2 RA3"
                else:  # GREEN
                    final_move = "GA2 GA3"
                print(colored(f"Using default fallback move: {final_move}", "yellow"))
        
        # If the final move still has the special tokens, extract just the move
        if isinstance(final_move, str) and "<<MOVE>>" in final_move and "<<END_MOVE>>" in final_move:
            move_match = re.search(r'<<MOVE>>([^<]+)<<END_MOVE>>', final_move)
            if move_match:
                final_move = move_match.group(1).strip()
                print(colored(f"Extracted move from special format: {final_move}", "green"))
        
        # Ensure move is properly formatted
        if final_move and " " not in final_move:
            # If the move doesn't contain a space, try to format it properly
            if len(final_move) == 6:  # Likely just missing space (e.g., "RB1RC3")
                final_move = final_move[:3] + " " + final_move[3:]
                print(colored(f"Reformatted move: {final_move}", "yellow"))
        
        # Validate the move to ensure it has valid coordinates
        final_move = validate_and_process_move(final_move)
        if not final_move:
            print(colored("Move validation failed, using fallback move", "red"))
            if current_color == "BLUE":
                final_move = "BA2 BA3"
            elif current_color == "RED":
                final_move = "RA2 RA3"
            else:  # GREEN
                final_move = "GA2 GA3"
        
        # Store token usage and thinking stats
        token_usage = {
            "timestamp": timestamp,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "reasoning_tokens": reasoning_tokens,
            "total_tokens": total_tokens
        }
        
        thinking_stat = {
            "timestamp": timestamp,
            "elapsed_time": elapsed_time,
        }
        
        if reasoning_tokens > 0:
            thinking_ratio = reasoning_tokens / max(1, completion_tokens)
            thinking_stat["thinking_ratio"] = thinking_ratio
            print(colored(f"Thinking ratio: {thinking_ratio:.2f}", "cyan"))
        
        AGENT_MEMORY["token_usage"].append(token_usage)
        AGENT_MEMORY["thinking_stats"].append(thinking_stat)
        
        # Store the move in agent memory with reasoning
        move_data = {
            "timestamp": timestamp,
            "color": current_color,
            "move": final_move,
            "reasoning": reasoning_text,
            "thinking_time": elapsed_time,
            "valid": True  # This will be updated when validation occurs
        }
        AGENT_MEMORY["moves"].append(move_data)
        
        print(colored(f"LLM response: {final_move}", "green"))
        return final_move
    except Exception as e:
        print(colored(f"Error in get_llm_move: {str(e)}", "red"))
        traceback.print_exc()
        
        # Fallback move in case of any error
        if current_color == "BLUE":
            return "BA2 BA3"
        elif current_color == "RED":
            return "RA2 RA3"
        else:  # GREEN
            return "GA2 GA3"

@app.route('/get-move', methods=['POST'])
def get_move():
    print(colored("Received move request", "yellow"))
    data = request.json
    
    # Extract data from the request
    board_state = data.get('boardState', '')
    current_color = data.get('currentColor', '')
    error_feedback = data.get('errorFeedback', '')
    
    # Debug the incoming data
    print(colored(f"Processing move for {current_color}", "yellow"))
    if error_feedback:
        print(colored(f"With error feedback: {error_feedback}", "yellow"))
    
    # Use asyncio to call the async LLM function
    move = asyncio.run(get_llm_move(board_state, current_color, error_feedback))
    
    # Ensure move is not None or empty
    if move is None or move == "":
        print(colored("Warning: Empty move returned from get_llm_move, using fallback", "red"))
        # Use a safe fallback like a standard pawn move
        if current_color == "BLUE":
            move = "BA2 BA3"
        elif current_color == "RED":
            move = "RA2 RA3"
        else:  # GREEN
            move = "GA2 GA3"
    
    # Extract special format if present
    move_match = re.search(r'<<MOVE>>([^<]+)<<END_MOVE>>', move)
    if move_match:
        move = move_match.group(1).strip()
        print(colored(f"Extracted final special format move: {move}", "green"))
    
    # Final validation before returning
    validated_move = validate_and_process_move(move)
    if not validated_move:
        print(colored(f"Warning: Final validation failed for move: {move}, using fallback", "red"))
        if current_color == "BLUE":
            validated_move = "BA2 BA3"
        elif current_color == "RED":
            validated_move = "RA2 RA3"
        else:  # GREEN
            validated_move = "GA2 GA3"
        move = validated_move
    
    # Extract the reasoning for the most recent move
    reasoning = "No reasoning available"
    if AGENT_MEMORY["moves"]:
        reasoning = AGENT_MEMORY["moves"][-1].get("reasoning", "No reasoning available")
    
    print(colored(f"Returning move: {move}", "green"))
    print(colored(f"Reasoning length: {len(reasoning)} characters", "cyan"))
    
    return jsonify({
        "move": move,
        "reasoning": reasoning
    })

@app.route('/agent-memory', methods=['GET'])
def agent_memory():
    """
    Endpoint to access the agent's memory and thinking process.
    """
    print(colored("Agent memory accessed", "blue"))
    
    # Check if debug info is being stored correctly
    print(colored(f"Debug info count: {len(AGENT_MEMORY.get('debug_info', []))}", "blue"))
    print(colored(f"Moves count: {len(AGENT_MEMORY.get('moves', []))}", "blue"))
    
    # Calculate summary statistics
    stats = {
        "total_moves": len(AGENT_MEMORY["moves"]),
        "start_time": AGENT_MEMORY["start_time"],
        "current_time": datetime.now().isoformat(),
        "total_tokens": {
            "prompt": sum(item["prompt_tokens"] for item in AGENT_MEMORY["token_usage"]),
            "completion": sum(item["completion_tokens"] for item in AGENT_MEMORY["token_usage"]),
            "reasoning": sum(item["reasoning_tokens"] for item in AGENT_MEMORY["token_usage"] if "reasoning_tokens" in item),
            "total": sum(item["total_tokens"] for item in AGENT_MEMORY["token_usage"])
        },
        "average_thinking_time": sum(item["elapsed_time"] for item in AGENT_MEMORY["thinking_stats"]) / 
                               max(1, len(AGENT_MEMORY["thinking_stats"])),
        "average_thinking_ratio": sum(item["thinking_ratio"] for item in AGENT_MEMORY["thinking_stats"] if "thinking_ratio" in item) / 
                               max(1, sum(1 for item in AGENT_MEMORY["thinking_stats"] if "thinking_ratio" in item))
    }
    
    # Calculate move validity statistics
    valid_moves = sum(1 for move in AGENT_MEMORY["moves"] if move.get("valid", False))
    stats["move_validity"] = {
        "valid_moves": valid_moves,
        "invalid_moves": len(AGENT_MEMORY["moves"]) - valid_moves,
        "validity_percentage": (valid_moves / max(1, len(AGENT_MEMORY["moves"]))) * 100
    }
    
    # Prepare the response with memory and stats
    memory_data = {
        "stats": stats,
        "moves": AGENT_MEMORY["moves"],
        "token_usage": AGENT_MEMORY["token_usage"],
        "thinking_stats": AGENT_MEMORY["thinking_stats"],
        "debug_info": AGENT_MEMORY["debug_info"],
        "errors": AGENT_MEMORY.get("errors", [])
    }
    
    return jsonify(memory_data)

@app.route('/debug-info', methods=['GET'])
def debug_info():
    """
    Endpoint to get detailed debugging information about move validation.
    """
    print(colored("Debug info accessed", "blue"))
    return jsonify({
        "debug_info": AGENT_MEMORY["debug_info"],
        "moves": AGENT_MEMORY["moves"]
    })

@app.route('/', methods=['GET'])
def root():
    print(colored("Root endpoint accessed", "green"))
    return jsonify({"status": "ok", "message": "LLM Chess API is running"})

@app.route('/health', methods=['GET'])
def health_check():
    print(colored("Health check received", "green"))
    return jsonify({"status": "ok", "message": "LLM Chess API is healthy"})

@app.route('/langsmith-info', methods=['GET'])
def langsmith_info():
    print(colored("LangSmith info accessed", "green"))
    return jsonify({
        "enabled": langsmith_helper.tracing_enabled,
        "project": langsmith_helper.project,
        "api_key_configured": langsmith_helper.api_key is not None
    })

if __name__ == "__main__":
    try:
        print(colored(f"Starting LLM Chess API server on port {PORT}...", "green"))
        print(colored(f"Using LLM model: {MODEL}", "green"))
        app.run(host="0.0.0.0", port=PORT)
    except Exception as e:
        print(colored(f"Error starting server: {e}", "red"))
        sys.exit(1) 