import pytest
import os
from one_function_to_call_them_all import one_function_to_call_them_all
from termcolor import cprint

# Test messages
TEST_MESSAGES = [
    {"role": "user", "content": "Hello, how are you?"}
]

# Setup test API keys (you should set these in your environment before running tests)
TEST_API_KEYS = {
    "openai": "test-openai-key",
    "anthropic": "test-anthropic-key",
    "openrouter": "test-openrouter-key",
    "groq": "test-groq-key"
}

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables before each test"""
    original_env = {}
    try:
        # Store original environment variables
        for provider, key in TEST_API_KEYS.items():
            env_key = f"{provider.upper()}_API_KEY"
            original_env[env_key] = os.environ.get(env_key)
            os.environ[env_key] = key
        
        yield
    
    finally:
        # Restore original environment variables
        for env_key, value in original_env.items():
            if value is None:
                os.environ.pop(env_key, None)
            else:
                os.environ[env_key] = value

@pytest.mark.asyncio
async def test_missing_api_key():
    """Test behavior when API key is missing"""
    os.environ["OPENAI_API_KEY"] = ""
    
    with pytest.raises(Exception) as exc_info:
        await one_function_to_call_them_all(
            messages=TEST_MESSAGES,
            provider="openai"
        )
    assert "No API key found for openai" in str(exc_info.value)

@pytest.mark.asyncio
async def test_default_parameters():
    """Test that default parameters are set correctly"""
    try:
        await one_function_to_call_them_all(TEST_MESSAGES)
    except Exception as e:
        # We expect an API error here, but we want to make sure it's not due to wrong parameters
        assert any(msg in str(e).lower() for msg in ["api key", "authentication"])

@pytest.mark.asyncio
async def test_system_message():
    """Test system message handling"""
    system_msg = "You are a helpful assistant"
    try:
        await one_function_to_call_them_all(
            messages=TEST_MESSAGES,
            system_message=system_msg
        )
    except Exception as e:
        # We expect an API error, but parameters should be correct
        assert any(msg in str(e).lower() for msg in ["api key", "authentication"])

@pytest.mark.asyncio
async def test_anthropic_format():
    """Test Anthropic-specific formatting"""
    try:
        await one_function_to_call_them_all(
            messages=TEST_MESSAGES,
            provider="anthropic",
            system_message="You are a helpful assistant"
        )
    except Exception as e:
        # We expect an API error, but parameters should be correct
        assert any(msg in str(e).lower() for msg in ["api key", "authentication", "not found"])

@pytest.mark.asyncio
async def test_additional_params():
    """Test handling of additional parameters"""
    additional_params = {"stream": False, "presence_penalty": 0.6}
    try:
        await one_function_to_call_them_all(
            messages=TEST_MESSAGES,
            additional_params=additional_params
        )
    except Exception as e:
        # We expect an API error, but parameters should be correct
        assert any(msg in str(e).lower() for msg in ["api key", "authentication"])

@pytest.mark.asyncio
async def test_max_tokens():
    """Test max_tokens parameter"""
    try:
        await one_function_to_call_them_all(
            messages=TEST_MESSAGES,
            max_tokens=100
        )
    except Exception as e:
        # We expect an API error, but parameters should be correct
        assert any(msg in str(e).lower() for msg in ["api key", "authentication"])

@pytest.mark.asyncio
async def test_model_override():
    """Test model override functionality"""
    custom_model = "gpt-4o"
    try:
        await one_function_to_call_them_all(
            messages=TEST_MESSAGES,
            model=custom_model
        )
    except Exception as e:
        # We expect an API error, but parameters should be correct
        assert any(msg in str(e).lower() for msg in ["api key", "authentication"])

def test_constants():
    """Test that all required constants are defined"""
    from one_function_to_call_them_all import API_KEYS, DEFAULT_MODELS, BASE_URLS
    
    # Check if all providers have corresponding entries in constants
    providers = ["openai", "anthropic", "openrouter", "groq"]
    for provider in providers:
        assert provider in API_KEYS
        assert provider in DEFAULT_MODELS
        assert provider in BASE_URLS

if __name__ == "__main__":
    cprint("Running LLM Handler tests...", "yellow")
    pytest.main([__file__, "-v"]) 