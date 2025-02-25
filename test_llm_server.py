import requests
import json
from termcolor import cprint
import asyncio
import sys
import os

# Sample board state
SAMPLE_BOARD = """
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

async def test_llm_server():
    cprint("Testing LLM Server...", "blue")
    
    # Test data
    data = {
        "board_state": SAMPLE_BOARD,
        "color": "blue",
        "model_provider": "openai",
        "model_name": "gpt-4o"
    }
    
    try:
        # Send request to server
        cprint("Sending request to LLM server...", "yellow")
        response = requests.post("http://localhost:8000/get_move", json=data)
        
        if response.status_code == 200:
            result = response.json()
            cprint(f"Success! Received move:", "green")
            cprint(f"Start position: {result['start_position']}", "green")
            cprint(f"End position: {result['end_position']}", "green")
            cprint(f"Reasoning: {result['reasoning']}", "green")
            return True
        else:
            cprint(f"Error: HTTP {response.status_code}", "red")
            cprint(f"Response: {response.text}", "red")
            return False
            
    except Exception as e:
        cprint(f"Error connecting to server: {str(e)}", "red")
        return False

if __name__ == "__main__":
    cprint("ThreeChess LLM Server Test", "blue", attrs=["bold"])
    
    # Run the test
    asyncio.run(test_llm_server()) 