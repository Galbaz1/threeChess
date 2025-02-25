#!/usr/bin/env python3
import subprocess
import os
import sys
from termcolor import colored

def run_llm_agent():
    """
    Run the ThreeChess game with the LLM-based agent (GPT-4o).
    
    This function starts the API server, compiles the Java code, and runs a game
    with the LLM agent. It requires an OpenAI API key to be set as an environment 
    variable OPENAI_API_KEY.
    
    Prerequisites:
    - Java installed
    - Python 3.6+ with dependencies in requirements.txt installed
    - Valid OpenAI API key
    
    Returns:
        None
    """
    try:
        print(colored("Starting ThreeChess with LLM Agent...", "green"))
        subprocess.run(["python", "run_llm_agent.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(colored(f"Error running LLM agent: {e}", "red"))
    except KeyboardInterrupt:
        print(colored("\nExecution interrupted by user", "yellow"))

def run_random_game():
    """
    Run a ThreeChess game with three random agents.
    
    This function compiles the Java code and runs a game with three random agents.
    It's useful for testing the basic functionality of the game without requiring
    an LLM API connection.
    
    Prerequisites:
    - Java installed
    
    Returns:
        None
    """
    try:
        print(colored("Compiling Java code...", "cyan"))
        compile_cmd = "mkdir -p bin && javac -d bin src/threeChess/*.java src/threeChess/agents/*.java"
        subprocess.run(compile_cmd, shell=True, check=True)
        
        print(colored("Running game with random agents...", "green"))
        run_cmd = "java -cp bin/ threeChess.ThreeChess"
        subprocess.run(run_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(colored(f"Error running random game: {e}", "red"))
    except KeyboardInterrupt:
        print(colored("\nExecution interrupted by user", "yellow"))

def run_llm_vs_random():
    """
    Run a ThreeChess game with one LLM agent and two random agents.
    
    This function starts the API server, compiles the Java code, and runs a game
    with one LLM agent and two random agents. It requires an OpenAI API key to be 
    set as an environment variable OPENAI_API_KEY.
    
    Prerequisites:
    - Java installed
    - Python 3.6+ with dependencies in requirements.txt installed
    - Valid OpenAI API key
    
    Returns:
        None
    """
    # This function would need a modified ThreeChess.java to specify different agents
    # We could implement this by adding a custom game setup option
    print(colored("This feature requires modifications to ThreeChess.java", "yellow"))
    print(colored("You would need to modify the game setup to use different agents", "yellow"))

def analyze_game_results(game_log_file=None):
    """
    Analyze the results of ThreeChess games.
    
    This function parses game logs to extract statistics and insights about
    game outcomes, move patterns, and agent performance.
    
    Args:
        game_log_file (str, optional): Path to the game log file. If None,
                                        will look for the most recent log.
    
    Returns:
        None: Prints analysis to stdout
    """
    print(colored("Game analysis feature not yet implemented", "yellow"))
    print(colored("This would analyze game logs for patterns and statistics", "yellow"))

def help():
    """
    Display help information about available tools.
    
    Returns:
        None: Prints help information to stdout
    """
    print(colored("\n=== ThreeChess Tools ===", "green"))
    print(colored("\nAvailable functions:", "cyan"))
    print(colored("  run_llm_agent()         - Run a game with the LLM agent", "white"))
    print(colored("  run_random_game()       - Run a game with three random agents", "white"))
    print(colored("  run_llm_vs_random()     - Run a game with one LLM agent and two random agents", "white"))
    print(colored("  analyze_game_results()  - Analyze game statistics and patterns", "white"))
    print(colored("  help()                  - Display this help message", "white"))
    
    print(colored("\nExample usage:", "cyan"))
    print(colored("  from tools import run_llm_agent", "white"))
    print(colored("  run_llm_agent()", "white"))
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        help()
    elif sys.argv[1] == "llm":
        run_llm_agent()
    elif sys.argv[1] == "random":
        run_random_game()
    elif sys.argv[1] == "analyze":
        analyze_game_results()
    else:
        help() 