import requests
from termcolor import cprint

def test_webapp_response():
    """Test if the web app is responding correctly"""
    try:
        cprint("Testing web app connection...", "blue")
        response = requests.get("http://localhost:5050")
        cprint(f"Status code: {response.status_code}", "green")
        
        if response.status_code == 200:
            cprint("Web app is running correctly!", "green")
            # Print first 100 characters of the response to verify
            cprint(f"Response preview: {response.text[:100]}...", "cyan")
        else:
            cprint(f"Error: Unexpected status code {response.status_code}", "red")
            cprint(f"Response: {response.text}", "red")
    except Exception as e:
        cprint(f"Error connecting to web app: {str(e)}", "red")
        
def test_llm_server_response():
    """Test if the LLM server is responding correctly"""
    try:
        cprint("\nTesting LLM server connection...", "blue")
        # We'll use the /docs endpoint which exists in FastAPI
        response = requests.get("http://localhost:8000/docs")
        cprint(f"Status code: {response.status_code}", "green")
        
        if response.status_code == 200:
            cprint("LLM server is running correctly!", "green")
        else:
            cprint(f"Error: Unexpected status code {response.status_code}", "red")
    except Exception as e:
        cprint(f"Error connecting to LLM server: {str(e)}", "red")

if __name__ == "__main__":
    test_webapp_response()
    test_llm_server_response() 