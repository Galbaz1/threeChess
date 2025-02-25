#!/usr/bin/env python3
import subprocess
import time
import os
import signal
import sys
from termcolor import colored

# CONSTANTS
PORT = 5002
API_SCRIPT = "llm_chess_api.py"
COMPILE_CMD = "mkdir -p bin && javac -d bin src/threeChess/*.java src/threeChess/agents/*.java"
RUN_CMD = "java -cp bin/ threeChess.ThreeChess llm"

def print_header():
    print(colored("\n╔════════════════════════════════════════════════════╗", "blue"))
    print(colored("║              ThreeChess with LLM Agent             ║", "blue"))
    print(colored("╚════════════════════════════════════════════════════╝\n", "blue"))

def check_openai_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(colored("ERROR: OPENAI_API_KEY environment variable is not set!", "red"))
        print(colored("Please set your OpenAI API key with:", "yellow"))
        print(colored("export OPENAI_API_KEY=your_api_key_here", "yellow"))
        return False
    return True

def install_requirements():
    print(colored("Installing required packages...", "cyan"))
    try:
        subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
        print(colored("✅ Requirements installed successfully", "green"))
        return True
    except subprocess.CalledProcessError as e:
        print(colored(f"❌ Error installing requirements: {e}", "red"))
        return False

def start_api_server():
    print(colored("Starting LLM API server...", "cyan"))
    try:
        process = subprocess.Popen(["python", API_SCRIPT])
        print(colored("✅ API server started", "green"))
        time.sleep(2)  # Give server time to start
        return process
    except Exception as e:
        print(colored(f"❌ Error starting API server: {e}", "red"))
        return None

def compile_java():
    print(colored("Compiling Java code...", "cyan"))
    try:
        result = subprocess.run(COMPILE_CMD, shell=True, check=True, capture_output=True, text=True)
        print(colored("✅ Compilation successful", "green"))
        return True
    except subprocess.CalledProcessError as e:
        print(colored(f"❌ Compilation failed: {e.stderr}", "red"))
        return False

def run_game():
    print(colored("Starting the game...", "cyan"))
    try:
        game_process = subprocess.run(RUN_CMD, shell=True)
        return True
    except Exception as e:
        print(colored(f"❌ Error running game: {e}", "red"))
        return False

def main():
    print_header()
    
    # Check for OpenAI API key
    if not check_openai_key():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Start API server
    api_process = start_api_server()
    if not api_process:
        sys.exit(1)
    
    try:
        # Compile Java code
        if not compile_java():
            api_process.terminate()
            sys.exit(1)
        
        # Run the game
        run_game()
        
    finally:
        # Clean up
        print(colored("\nShutting down API server...", "cyan"))
        api_process.terminate()
        print(colored("✅ API server stopped", "green"))
        print(colored("\nThank you for playing ThreeChess with LLM Agent!", "magenta"))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored("\nInterrupted by user. Exiting...", "yellow"))
        sys.exit(0) 