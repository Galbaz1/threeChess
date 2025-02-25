from flask import Flask, render_template, request, jsonify, redirect, url_for
import asyncio
import requests
import json
import pygame
import io
import base64
import time
import math
from termcolor import cprint
import os
import sys

# Import our existing game logic
from simulate_game import SimpleBoard, get_move_from_llm, INITIAL_BOARD, PLAYERS

# Configure constants
API_URL = "http://localhost:8000/get_move"
REFRESH_INTERVAL = 3000  # milliseconds for frontend refresh

app = Flask(__name__)

# Global variables to store game state
current_game = None
move_history = []
background_tasks = {}

class WebGame:
    def __init__(self):
        self.board = SimpleBoard(INITIAL_BOARD)
        self.status = "ready"  # ready, running, finished
        self.current_move = None
        self.move_history = []
        self.players = PLAYERS.copy()  # Default players
        self.renderer = BoardRenderer()
        self.error = None
        
    async def make_move(self):
        if self.status != "running":
            return False
            
        color = self.board.turn
        cprint(f"Getting move for {color} using {self.players[color]['provider']}-{self.players[color]['model']}", "blue")
        
        try:
            start_pos, end_pos, reasoning = await get_move_from_llm(self.board, color, api_url=API_URL)
            
            if start_pos and end_pos:
                self.board.make_move(start_pos, end_pos)
                self.move_history.append({
                    "color": color,
                    "start": start_pos,
                    "end": end_pos,
                    "reasoning": reasoning,
                    "timestamp": time.time()
                })
                self.error = None
                return True
            else:
                self.error = f"Failed to get a valid move for {color}"
                cprint(self.error, "red")
                return False
        except Exception as e:
            self.error = f"Error making move: {str(e)}"
            cprint(self.error, "red")
            return False
        
    def get_board_image(self):
        """Get the current board state as a base64 encoded PNG image"""
        try:
            return self.renderer.render_board(self.board)
        except Exception as e:
            cprint(f"Error rendering board: {str(e)}", "red")
            return None
        
    def reset(self):
        """Reset the game to the initial state"""
        self.board = SimpleBoard(INITIAL_BOARD)
        self.status = "ready"
        self.current_move = None
        self.move_history = []
        self.error = None
        
class BoardRenderer:
    def __init__(self):
        # Initialize pygame
        pygame.init()
        
        # Constants for three-player chess
        self.SQUARE_SIZE = 50
        self.BOARD_WIDTH = 800
        self.BOARD_HEIGHT = 800
        
        # Colors for the three players and board
        self.WHITE = (255, 255, 255)
        self.BLACK = (40, 40, 40)
        self.BLUE_LIGHT = (173, 216, 230)
        self.BLUE_DARK = (0, 0, 139)
        self.GREEN_LIGHT = (144, 238, 144)
        self.GREEN_DARK = (0, 100, 0)
        self.RED_LIGHT = (255, 182, 193)
        self.RED_DARK = (139, 0, 0)
        self.BACKGROUND = (245, 245, 245)
        
        # Create a surface for the board
        self.surface = pygame.Surface((self.BOARD_WIDTH, self.BOARD_HEIGHT))
        
        # Calculate board coordinates
        self.calculate_board_coordinates()
        
    def calculate_board_coordinates(self):
        """Calculate coordinates for the triangular three-player chess board"""
        # Center point of the board
        center_x = self.BOARD_WIDTH // 2
        center_y = self.BOARD_HEIGHT // 2
        
        # Calculate the coordinates for the three sections of the board
        self.sections = {
            "BLUE": self._create_section(center_x, center_y, 0),  # Blue at bottom
            "GREEN": self._create_section(center_x, center_y, 1), # Green at top right
            "RED": self._create_section(center_x, center_y, 2)    # Red at top left
        }
        
    def _create_section(self, center_x, center_y, section_idx):
        """Create coordinates for one section of the board (one player's territory)"""
        # Radius of the board from center to corner
        radius = min(self.BOARD_WIDTH, self.BOARD_HEIGHT) * 0.45
        
        # Calculate the starting angle for this section
        base_angle = (section_idx * 120 - 90) % 360
        
        # Create the outer points of this section
        outer_points = []
        for i in range(5):
            angle_rad = math.radians(base_angle + i * 30)
            x = center_x + radius * math.cos(angle_rad)
            y = center_y + radius * math.sin(angle_rad)
            outer_points.append((int(x), int(y)))
        
        # Store all squares in this section
        squares = {}
        
        # Create 4x8 grid of squares for this section
        for row in range(4):
            for col in range(8):
                # Calculate the position label (a1, b2, etc)
                pos_label = f"{chr(97 + col)}{row + 1}"
                
                # Calculate the square's corner points
                points = self._calculate_square_points(center_x, center_y, section_idx, row, col, radius)
                
                # Calculate center point of the square
                center_pt = self._calculate_center_point(points)
                
                # Store the square data
                squares[pos_label] = {
                    "points": points,
                    "center": center_pt,
                    "colored": (row + col) % 2 == 0  # Alternating colors
                }
        
        return {
            "outer_points": outer_points,
            "squares": squares,
            "idx": section_idx
        }
    
    def _calculate_square_points(self, center_x, center_y, section_idx, row, col, radius):
        """Calculate the four corner points of a square in the triangular grid"""
        # Base angle for this section
        base_angle = (section_idx * 120 - 90) % 360
        
        # Scale factors for the grid
        row_scale = 0.1
        col_scale = 0.05
        
        # Calculate the square's position relative to the center
        angle1_rad = math.radians(base_angle + col * col_scale * 30)
        angle2_rad = math.radians(base_angle + (col + 1) * col_scale * 30)
        
        # Outer radius for this row
        r1 = radius * (0.7 - row * row_scale)
        r2 = radius * (0.7 - (row + 1) * row_scale)
        
        # Calculate the four corners
        p1 = (int(center_x + r1 * math.cos(angle1_rad)), int(center_y + r1 * math.sin(angle1_rad)))
        p2 = (int(center_x + r1 * math.cos(angle2_rad)), int(center_y + r1 * math.sin(angle2_rad)))
        p3 = (int(center_x + r2 * math.cos(angle2_rad)), int(center_y + r2 * math.sin(angle2_rad)))
        p4 = (int(center_x + r2 * math.cos(angle1_rad)), int(center_y + r2 * math.sin(angle1_rad)))
        
        return [p1, p2, p3, p4]
    
    def _calculate_center_point(self, points):
        """Calculate the center point of a polygon"""
        x_sum = sum(p[0] for p in points)
        y_sum = sum(p[1] for p in points)
        return (x_sum // len(points), y_sum // len(points))
    
    def render_board(self, board):
        """Render the board state to a PNG image and return as base64"""
        # Fill background
        self.surface.fill(self.BACKGROUND)
        
        # Parse board string to determine piece positions
        piece_positions = self._parse_board_string(board.board_str)
        
        # Draw the three sections of the board
        for color, section in self.sections.items():
            self._draw_section(color, section, piece_positions)
        
        # Convert surface to PNG
        png_bytes = io.BytesIO()
        pygame.image.save(self.surface, png_bytes)
        png_bytes.seek(0)
        
        # Convert to base64
        return base64.b64encode(png_bytes.read()).decode('utf-8')
    
    def _draw_section(self, color, section, piece_positions):
        """Draw one section of the three-player board"""
        # Determine section colors
        if color == "BLUE":
            light_color = self.BLUE_LIGHT
            dark_color = self.BLUE_DARK
        elif color == "GREEN":
            light_color = self.GREEN_LIGHT
            dark_color = self.GREEN_DARK
        else:  # RED
            light_color = self.RED_LIGHT
            dark_color = self.RED_DARK
        
        # Draw each square in this section
        for pos, square_data in section["squares"].items():
            # Determine square color
            square_color = light_color if square_data["colored"] else dark_color
            
            # Draw the square
            pygame.draw.polygon(self.surface, square_color, square_data["points"])
            
            # Draw piece if there is one at this position
            if pos in piece_positions:
                self._draw_piece(square_data["center"], piece_positions[pos])
    
    def _parse_board_string(self, board_str):
        """Parse the text representation of the board to get piece positions"""
        piece_positions = {}
        lines = board_str.strip().split('\n')
        
        # Skip header lines
        board_lines = [line for line in lines if line.strip() and line[0].isdigit()]
        
        for i, line in enumerate(board_lines):
            rank = 8 - i  # Ranks go from 8 to 1
            parts = line.strip().split()
            
            # Skip the rank number
            parts = parts[1:]
            
            for j, piece in enumerate(parts):
                if piece != '·':
                    file = chr(97 + j)  # Files go from a to h
                    piece_positions[f"{file}{rank}"] = piece
                    
        return piece_positions
        
    def _draw_piece(self, center, piece_info):
        """Draw a chess piece on the board"""
        # Parse piece info: first char is color, second is piece type
        if len(piece_info) < 2:
            return
            
        color_char = piece_info[0]
        piece_char = piece_info[1]
        
        # Set the piece color
        if color_char == 'B':
            piece_color = self.BLUE_DARK
        elif color_char == 'G':
            piece_color = self.GREEN_DARK
        elif color_char == 'R':
            piece_color = self.RED_DARK
        else:
            return
            
        # Draw circle for the piece
        pygame.draw.circle(self.surface, piece_color, center, self.SQUARE_SIZE // 2.5)
        
        # Add piece type label
        font = pygame.font.SysFont('Arial', 20)
        text = font.render(piece_char, True, self.WHITE)
        text_rect = text.get_rect(center=center)
        self.surface.blit(text, text_rect)

async def background_move_task(game_id):
    """Background task to continuously make moves"""
    global current_game
    
    if not current_game:
        return
        
    while current_game.status == "running":
        success = await current_game.make_move()
        
        if not success and current_game.error:
            cprint(f"Move failed: {current_game.error}", "red")
            # Don't stop the game, just continue to the next player
            current_game.board.turn = "GREEN" if current_game.board.turn == "BLUE" else ("RED" if current_game.board.turn == "GREEN" else "BLUE")
            
        # Small delay between moves
        await asyncio.sleep(2)

# Routes
@app.route('/')
def index():
    global current_game
    
    # Initialize game if not exists
    if current_game is None:
        current_game = WebGame()
        
    # Get board image
    board_image = current_game.get_board_image()
    
    return render_template('index.html', 
                          board_image=board_image,
                          board=current_game.board,
                          players=current_game.players,
                          game_status=current_game.status,
                          move_history=current_game.move_history,
                          error=current_game.error)

@app.route('/start_game', methods=['POST'])
def start_game():
    global current_game, background_tasks
    
    # Set up players based on form data
    if request.method == 'POST':
        try:
            blue_provider = request.form.get('blue_provider', 'openai')
            blue_model = request.form.get('blue_model', 'gpt-4o')
            green_provider = request.form.get('green_provider', 'anthropic')
            green_model = request.form.get('green_model', 'claude-3-5-sonnet-latest')
            red_provider = request.form.get('red_provider', 'openrouter')
            red_model = request.form.get('red_model', 'google/gemini-flash-1.5-8b')
            
            # Update game players
            current_game.players = {
                "BLUE": {"provider": blue_provider, "model": blue_model},
                "GREEN": {"provider": green_provider, "model": green_model},
                "RED": {"provider": red_provider, "model": red_model}
            }
            
            # Set game to running
            current_game.status = "running"
            current_game.error = None
            
            # Start background task for moves
            game_id = str(int(time.time()))
            
            # Use a separate thread to run the asyncio loop
            def run_background_task():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(background_move_task(game_id))
                
            import threading
            task_thread = threading.Thread(target=run_background_task)
            task_thread.daemon = True
            task_thread.start()
            background_tasks[game_id] = task_thread
            
            cprint(f"Started game with players: {current_game.players}", "green")
        except Exception as e:
            current_game.error = f"Error starting game: {str(e)}"
            cprint(current_game.error, "red")
    
    return redirect(url_for('index'))

@app.route('/make_move', methods=['POST'])
def make_move():
    global current_game
    
    if current_game and current_game.status == "running":
        try:
            # Make a single move - useful for manual mode
            asyncio.run(current_game.make_move())
        except Exception as e:
            current_game.error = f"Error making move: {str(e)}"
            cprint(current_game.error, "red")
        
    return redirect(url_for('index'))

@app.route('/reset_game', methods=['POST'])
def reset_game():
    global current_game, background_tasks
    
    if current_game:
        current_game.reset()
        # Stop any background tasks
        for task_id, thread in list(background_tasks.items()):
            background_tasks.pop(task_id, None)
        
    return redirect(url_for('index'))

@app.route('/board_image')
def board_image():
    global current_game
    
    if current_game:
        image = current_game.get_board_image()
        if image:
            return jsonify({"image": image})
    
    return jsonify({"error": "No game in progress or error rendering board"})

@app.route('/game_status')
def game_status():
    global current_game
    
    if current_game:
        return jsonify({
            "status": current_game.status,
            "turn": current_game.board.turn,
            "move_count": current_game.board.move_count,
            "last_move": current_game.move_history[-1] if current_game.move_history else None,
            "error": current_game.error
        })
    
    return jsonify({"error": "No game in progress"})

if __name__ == '__main__':
    cprint("Starting ThreeChess Web App...", "green")
    
    # Ensure the templates directory exists
    os.makedirs('templates', exist_ok=True)
    
    # Start the Flask app
    app.run(debug=True, port=5050) 