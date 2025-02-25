from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
from termcolor import cprint
import sys
import os

# Import the LLM function
sys.path.append(os.path.join(os.path.dirname(__file__), "call_all"))
from one_function_to_call_them_all import one_function_to_call_them_all

app = FastAPI(title="ThreeChess LLM Server")

class MoveRequest(BaseModel):
    board_state: str
    color: str
    model_provider: str = "openai"
    model_name: Optional[str] = None
    
class MoveResponse(BaseModel):
    start_position: str
    end_position: str
    reasoning: Optional[str] = None

SYSTEM_PROMPT = """
You are playing three-player chess. The board has been modified to accommodate three players, with each player controlling pieces of a different color (blue, green, or red). 
Your task is to analyze the current board state and select the best move for your color.

Three-player chess rules:
1. Pieces move the same way as in regular chess
2. The first player to lose their king loses the game
3. After a player loses, their remaining pieces are immobilized
4. The goal is to capture an opponent's king

Respond with:
1. The start position (e.g. "b1")
2. The end position (e.g. "c3")
3. A brief explanation of your reasoning

Format your response as:
START: [start position]
END: [end position]
REASONING: [your reasoning]
"""

@app.post("/get_move", response_model=MoveResponse)
async def get_move(request: MoveRequest):
    try:
        cprint(f"Received move request for {request.color} player using {request.model_provider} model", "blue")
        
        # Prepare messages for the LLM
        messages = [
            {"role": "user", "content": f"""
Board State:
{request.board_state}

You are playing as {request.color}. What is your next move?
Please analyze the board carefully and make a legal move.
"""
            }
        ]
        
        # Call the LLM
        response = await one_function_to_call_them_all(
            messages=messages,
            provider=request.model_provider,
            model=request.model_name,
            system_message=SYSTEM_PROMPT
        )
        
        cprint(f"LLM response: {response}", "green")
        
        # Parse the response
        start_pos = None
        end_pos = None
        reasoning = None
        
        for line in response.split('\n'):
            if line.startswith("START:"):
                start_pos = line.replace("START:", "").strip()
            elif line.startswith("END:"):
                end_pos = line.replace("END:", "").strip()
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
                
        if not start_pos or not end_pos:
            # Try to extract positions from text if standard format wasn't used
            import re
            positions = re.findall(r'\b([a-h][1-8])\b', response)
            if len(positions) >= 2:
                start_pos = positions[0]
                end_pos = positions[1]
                reasoning = "Extracted from text"
        
        if not start_pos or not end_pos:
            raise ValueError("Could not parse a valid move from LLM response")
            
        return MoveResponse(
            start_position=start_pos,
            end_position=end_pos,
            reasoning=reasoning or "No reasoning provided"
        )
    
    except Exception as e:
        cprint(f"Error processing move: {str(e)}", "red")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    cprint("Starting ThreeChess LLM Server...", "green")
    uvicorn.run(app, host="0.0.0.0", port=8000) 