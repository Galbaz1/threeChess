from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from termcolor import cprint
import os
import json

# Constants
API_KEYS = {
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "openrouter": os.getenv("OPENROUTER_API_KEY"),
    "groq": os.getenv("GROQ_API_KEY")
}

DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "anthropic": "claude-3-5-sonnet-latest",
    "openrouter": "google/gemini-flash-1.5-8b",
    "groq": "llama-3.3-70b-versatile"
}

BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": None,  # Anthropic uses its own client
    "openrouter": "https://openrouter.ai/api/v1",
    "groq": "https://api.groq.com/openai/v1"
}

def get_api_key(provider: str) -> str:
    """Get API key for the specified provider from environment variables"""
    return os.getenv(f"{provider.upper()}_API_KEY", "")

async def one_function_to_call_them_all(
    messages: List[Dict[str, str]],
    provider: str = "openai",
    model: Optional[str] = "gpt-4o",
    system_message: Optional[str] = None,
    max_tokens: Optional[int] = None,
    additional_params: Optional[Dict[str, Any]] = None
) -> str:
    """
    Universal function to call any supported LLM provider.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        provider: The LLM provider to use
        model: Specific model to use (defaults to provider's default)
        system_message: System message for providers that support it
        temperature: Controls randomness in the response
        max_tokens: Maximum tokens in the response
        additional_params: Any additional parameters specific to the provider
    
    Returns:
        str: The generated response
    """
    try:
        cprint(f"Initializing {provider} client...", "blue")
        
        api_key = get_api_key(provider)
        if not api_key or api_key.strip() == "":
            raise ValueError(f"No API key found for {provider}")

        # Get the default model for the provider if none specified
        if not model or model == "gpt-4o":  # If default OpenAI model, use provider's default
            model = DEFAULT_MODELS[provider]
        
        # Handle Anthropic separately as it uses its own client
        if provider == "anthropic":
            client = AsyncAnthropic(api_key=api_key)
            
            # Convert messages to Anthropic format
            messages_text = "\n\n".join([f"{m['role']}: {m['content']}" for m in messages])
            
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens or 8000,
                system=system_message,
                messages=[{"role": "user", "content": messages_text}],
                **(additional_params or {})
            )
            cprint("Successfully received response from Anthropic", "green")
            return response.content[0].text

        # Handle other providers using OpenAI client
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=BASE_URLS[provider]
        )

        # Prepare parameters
        params = {
            "model": model,
            "messages": messages if not system_message else [{"role": "system", "content": system_message}, *messages],
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
            
        if additional_params:
            params.update(additional_params)

        cprint(f"Sending request to {provider} with model {model}...", "yellow")
        
        response = await client.chat.completions.create(**params)
        
        cprint(f"Successfully received response from {provider}", "green")
        return response.choices[0].message.content

    except Exception as e:
        error_msg = f"Error calling {provider} LLM: {str(e)}"
        cprint(error_msg, "red")
        raise Exception(error_msg) 