import os
import time
from dotenv import load_dotenv
from jeanmemory import JeanMemoryClient

# Load environment variables from .env file
load_dotenv()

def test_speed_modes():
    """
    Tests the different speed modes of the Jean Memory API.
    """
    api_key = os.getenv("JEAN_MEMORY_API_KEY")
    if not api_key:
        print("Error: JEAN_MEMORY_API_KEY environment variable not set.")
        print("Please set it to your Jean Memory API key.")
        return

    client = JeanMemoryClient(api_key=api_key)
    
    query = "What have I been working on recently?"
    
    modes = ["autonomous"]
    
    for mode in modes:
        print(f"--- Testing mode: {mode} ---")
        start_time = time.time()
        try:
            # The get_context method is synchronous in the Python SDK
            result = client.get_context(query=query, speed=mode)
            end_time = time.time()
            latency = end_time - start_time
            
            print(f"Result for '{mode}' mode (took {latency:.2f}s):")
            # Assuming the result has a 'to_dict()' method or is directly printable
            if hasattr(result, 'to_dict'):
                print(result.to_dict())
            else:
                print(result)
            print("-" * (len(mode) + 18))
            print("\n")
            
        except Exception as e:
            end_time = time.time()
            latency = end_time - start_time
            print(f"Error testing '{mode}' mode (took {latency:.2f}s): {e}")
            print("-" * (len(mode) + 18))
            print("\n")

if __name__ == "__main__":
    test_speed_modes()
