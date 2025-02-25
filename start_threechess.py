#!/usr/bin/env python
import subprocess
import sys
import os
import time
from termcolor import cprint
import signal
import atexit

# Constants
LLM_SERVER_PORT = 8000
WEB_APP_PORT = 5050

# Global variables to track processes
processes = []

def cleanup():
    """Kill all child processes on exit"""
    cprint("Shutting down ThreeChess servers...", "yellow")
    for process in processes:
        try:
            if process.poll() is None:  # If process is still running
                process.terminate()
                cprint(f"Terminated process {process.pid}", "yellow")
        except Exception as e:
            cprint(f"Error terminating process: {str(e)}", "red")

def start_llm_server():
    """Start the LLM server"""
    try:
        cprint("Starting LLM Server on port 8000...", "blue")
        process = subprocess.Popen(
            [sys.executable, "llm_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(process)
        
        # Wait for server to start
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
            if "Uvicorn running on" in line:
                cprint("LLM Server started successfully!", "green")
                break
            
        return process
    except Exception as e:
        cprint(f"Error starting LLM server: {str(e)}", "red")
        return None

def start_web_app():
    """Start the web application"""
    try:
        cprint("Starting Web App on port 5050...", "blue")
        process = subprocess.Popen(
            [sys.executable, "web_app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(process)
        
        # Wait for server to start
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
            if "Running on" in line and "5050" in line:
                cprint("Web App started successfully!", "green")
                cprint(f"Open your browser at http://localhost:{WEB_APP_PORT}", "green")
                break
            
        return process
    except Exception as e:
        cprint(f"Error starting web app: {str(e)}", "red")
        return None

def check_ports():
    """Check if the required ports are available"""
    import socket
    
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
            
    if is_port_in_use(LLM_SERVER_PORT):
        cprint(f"Port {LLM_SERVER_PORT} is already in use. Please free this port before starting.", "red")
        return False
        
    if is_port_in_use(WEB_APP_PORT):
        cprint(f"Port {WEB_APP_PORT} is already in use. Please free this port before starting.", "red")
        return False
        
    return True

def main():
    """Main function to start all servers"""
    cprint("=== ThreeChess LLM Arena ===", "blue", attrs=["bold"])
    
    # Register cleanup function
    atexit.register(cleanup)
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        cprint("\nCtrl+C detected. Shutting down...", "yellow")
        cleanup()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check if ports are available
    if not check_ports():
        sys.exit(1)
    
    # Start LLM server
    llm_server = start_llm_server()
    if not llm_server:
        cprint("Failed to start LLM server. Exiting.", "red")
        sys.exit(1)
        
    # Give the LLM server a moment to fully initialize
    time.sleep(2)
    
    # Start web app
    web_app = start_web_app()
    if not web_app:
        cprint("Failed to start web app. Exiting.", "red")
        sys.exit(1)
    
    cprint("\nAll servers started successfully!", "green", attrs=["bold"])
    cprint("Press Ctrl+C to shut down all servers.", "yellow")
    
    # Keep the script running
    try:
        while True:
            # Check if any process has terminated
            if llm_server.poll() is not None:
                cprint("LLM server has stopped. Shutting down...", "red")
                break
                
            if web_app.poll() is not None:
                cprint("Web app has stopped. Shutting down...", "red")
                break
                
            time.sleep(1)
    except KeyboardInterrupt:
        cprint("\nShutting down...", "yellow")
    finally:
        cleanup()

if __name__ == "__main__":
    main() 