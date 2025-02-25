import os
import time
from termcolor import colored
from openai import OpenAI, AsyncOpenAI
from langsmith.wrappers import wrap_openai
from langsmith import traceable
from typing import Optional, Dict, Any, Union, List

# Constants for LangSmith configuration
LANGSMITH_API_KEY = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
LANGSMITH_TRACING = os.getenv("LANGCHAIN_TRACING_V2") == "true" or os.getenv("LANGSMITH_TRACING") == "true"
LANGSMITH_PROJECT = os.getenv("LANGCHAIN_PROJECT") or os.getenv("LANGSMITH_PROJECT", "chess")
LANGSMITH_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT") or os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

class LangSmithHelper:
    """Helper class for LangSmith integration with robust error handling."""
    
    def __init__(self, api_key: Optional[str] = None, project: Optional[str] = None, 
                 tracing_enabled: Optional[bool] = None, verbose: bool = True):
        """
        Initialize the LangSmith helper.
        
        Args:
            api_key: LangSmith API key (overrides environment variable)
            project: LangSmith project name (overrides environment variable)
            tracing_enabled: Whether to enable tracing (overrides environment variable)
            verbose: Whether to print verbose output
        """
        self.api_key = api_key or LANGSMITH_API_KEY
        self.project = project or LANGSMITH_PROJECT
        self.tracing_enabled = tracing_enabled if tracing_enabled is not None else LANGSMITH_TRACING
        self.verbose = verbose
        self.sync_client = None
        self.async_client = None
        self.wrapped_sync_client = None
        self.wrapped_async_client = None
        self.is_initialized = False
        
        # Set environment variables if provided
        if self.api_key:
            os.environ["LANGCHAIN_API_KEY"] = self.api_key
        if self.project:
            os.environ["LANGCHAIN_PROJECT"] = self.project
        if self.tracing_enabled:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
        
        if self.verbose:
            self._print_config()
    
    def _print_config(self):
        """Print the current LangSmith configuration."""
        print(colored("LangSmith Configuration", "yellow"))
        print(colored("======================", "yellow"))
        print(colored(f"API Key: {self.api_key[:10]}... (masked)" if self.api_key else "API Key: Not set", "cyan"))
        print(colored(f"Project: {self.project}", "cyan"))
        print(colored(f"Tracing Enabled: {self.tracing_enabled}", "cyan"))
        print(colored(f"Endpoint: {LANGSMITH_ENDPOINT}", "cyan"))
    
    def initialize(self, openai_api_key: Optional[str] = None) -> bool:
        """
        Initialize the OpenAI clients with LangSmith wrapping.
        
        Args:
            openai_api_key: OpenAI API key (uses environment variable if not provided)
            
        Returns:
            bool: Whether initialization was successful
        """
        try:
            if self.verbose:
                print(colored("\nInitializing OpenAI clients...", "yellow"))
            
            # Initialize sync client
            self.sync_client = OpenAI(api_key=openai_api_key)
            
            # Initialize async client
            self.async_client = AsyncOpenAI(api_key=openai_api_key)
            
            # Wrap clients with LangSmith if tracing is enabled
            if self.tracing_enabled and self.api_key:
                try:
                    self.wrapped_sync_client = wrap_openai(self.sync_client)
                    self.wrapped_async_client = wrap_openai(self.async_client)
                    if self.verbose:
                        print(colored("Successfully wrapped OpenAI clients with LangSmith", "green"))
                except Exception as e:
                    if self.verbose:
                        print(colored(f"Warning: Failed to wrap OpenAI clients with LangSmith: {str(e)}", "yellow"))
                    # Fall back to unwrapped clients
                    self.wrapped_sync_client = self.sync_client
                    self.wrapped_async_client = self.async_client
            else:
                # Use unwrapped clients if tracing is disabled
                self.wrapped_sync_client = self.sync_client
                self.wrapped_async_client = self.async_client
                if self.verbose:
                    print(colored("Using OpenAI clients without LangSmith tracing", "yellow"))
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            if self.verbose:
                print(colored(f"Error initializing OpenAI clients: {str(e)}", "red"))
            return False
    
    def get_sync_client(self) -> OpenAI:
        """Get the wrapped synchronous OpenAI client."""
        if not self.is_initialized:
            self.initialize()
        return self.wrapped_sync_client
    
    def get_async_client(self) -> AsyncOpenAI:
        """Get the wrapped asynchronous OpenAI client."""
        if not self.is_initialized:
            self.initialize()
        return self.wrapped_async_client
    
    @staticmethod
    def create_traceable_function(func_name: str, run_type: str = "chain"):
        """
        Create a decorator for tracing a function with LangSmith.
        
        Args:
            func_name: Name of the function for tracing
            run_type: Type of run (chain, llm, tool, etc.)
            
        Returns:
            Decorator function
        """
        return traceable(name=func_name, run_type=run_type)
    
    def handle_langsmith_error(self, error: Exception) -> str:
        """
        Handle LangSmith-related errors with helpful messages.
        
        Args:
            error: The exception that occurred
            
        Returns:
            str: A helpful error message
        """
        error_str = str(error)
        
        if "Rate limit exceeded" in error_str:
            message = "LangSmith rate limit exceeded. You can continue using the API without tracing."
            if self.verbose:
                print(colored(message, "yellow"))
            # Disable tracing to prevent further rate limit errors
            self.tracing_enabled = False
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            return message
        
        if "API key" in error_str.lower() and "invalid" in error_str.lower():
            message = "Invalid LangSmith API key. Check your API key and try again."
            if self.verbose:
                print(colored(message, "red"))
            return message
        
        # Generic error handling
        message = f"LangSmith error: {error_str}"
        if self.verbose:
            print(colored(message, "red"))
        return message

# Example usage
if __name__ == "__main__":
    # Initialize with the provided API key
    helper = LangSmithHelper(
        api_key="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",
        project="chess_test",
        tracing_enabled=True
    )
    
    # Initialize the clients
    if not helper.initialize():
        print(colored("Failed to initialize. Exiting.", "red"))
        exit(1)
    
    # Get the wrapped client
    client = helper.get_sync_client()
    
    # Define a traceable function
    @helper.create_traceable_function("ChessTest_SimpleQuery")
    def simple_query(prompt: str) -> str:
        """Simple query function with LangSmith tracing."""
        print(colored(f"Sending query: {prompt}", "yellow"))
        try:
            start_time = time.time()
            response = client.chat.completions.create(
                model="o3-mini",
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=100
            )
            elapsed_time = time.time() - start_time
            result = response.choices[0].message.content
            print(colored(f"Query time: {elapsed_time:.2f} seconds", "cyan"))
            return result
        except Exception as e:
            print(colored(f"Error in API call: {str(e)}", "red"))
            return f"Error: {str(e)}"
    
    # Test the function
    print(colored("\nTesting LangSmith tracing with a simple query...", "yellow"))
    result = simple_query("What's the best opening move in chess and why?")
    
    print(colored("\nResponse:", "green"))
    print(colored(result, "white"))
    
    print(colored("\nTest completed. Check your LangSmith dashboard at:", "yellow"))
    print(colored("https://smith.langchain.com/", "cyan"))
    print(colored(f"Look for the project: {helper.project}", "cyan")) 