import asyncio
from typing import List, Dict
from termcolor import cprint
import sys
from one_function_to_call_them_all import one_function_to_call_them_all, DEFAULT_MODELS

# Constants
PROVIDERS = {
    1: "openai",
    2: "anthropic",
    3: "openrouter",
    4: "groq"
}

def print_provider_options():
    """Print available provider options"""
    cprint("\nAvailable Providers:", "cyan")
    for num, provider in PROVIDERS.items():
        model = DEFAULT_MODELS[provider]
        cprint(f"{num}. {provider.upper()} (Default model: {model})", "cyan")

def get_provider_choice() -> str:
    """Get provider choice from user"""
    while True:
        try:
            print_provider_options()
            choice = int(input("\nSelect a provider (1-4): ").strip())
            if choice in PROVIDERS:
                selected = PROVIDERS[choice]
                cprint(f"\nSelected {selected.upper()} as your provider!", "green")
                return selected
            else:
                cprint("Invalid choice. Please select a number between 1-4.", "red")
        except ValueError:
            cprint("Please enter a valid number.", "red")

async def chat_session():
    """Main chat session handler"""
    cprint("\n=== Welcome to Multi-Provider Chat Interface ===", "magenta")
    cprint("Type '--switch' to change providers", "yellow")
    cprint("Type '--exit' to end chat", "yellow")
    
    # Initialize chat
    provider = get_provider_choice()
    messages: List[Dict[str, str]] = []
    
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        # Check for commands
        if user_input.lower() == '--exit':
            cprint("\nGoodbye!", "magenta")
            break
        elif user_input.lower() == '--switch':
            provider = get_provider_choice()
            continue
        
        # Add user message to history
        messages.append({"role": "user", "content": user_input})
        
        try:
            # Call LLM
            cprint("\nAssistant: ", "green", end="")
            response = await one_function_to_call_them_all(
                messages=messages,
                provider=provider
            )
            print(response)
            
            # Add assistant response to history
            messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            cprint(f"\nError: {str(e)}", "red")
            cprint("You can try switching to a different provider with '--switch'", "yellow")

def main():
    """Main entry point"""
    try:
        asyncio.run(chat_session())
    except KeyboardInterrupt:
        cprint("\nChat session terminated by user.", "magenta")
    except Exception as e:
        cprint(f"\nUnexpected error: {str(e)}", "red")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main() 