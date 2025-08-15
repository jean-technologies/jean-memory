import requests
import sys

# The URL where the file should be accessible when running `mintlify dev`
URL = "http://localhost:3000/static/consolidated-docs.md"

def run_test():
    """
    Attempts to fetch the consolidated documentation file from the local
    development server.
    """
    print(f"🧪 Testing access to {URL}...")
    try:
        response = requests.get(URL, timeout=10)
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: The file was fetched successfully!")
            print(f"   - Status Code: {response.status_code}")
            print(f"   - File size: {len(response.content)} bytes")
            if len(response.content) > 1000:
                print("   - Verification: File size looks reasonable.")
            else:
                print("   - WARNING: File seems small. Please verify its contents.")
            sys.exit(0)
        else:
            print(f"\n❌ FAILURE: Received an error status code.")
            print(f"   - Status Code: {response.status_code}")
            print("   - Please check if the file exists and the server is configured correctly.")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ FAILURE: Could not connect to the server at http://localhost:3000.")
        print("   - Is the Mintlify development server running?")
        print("   - Please run `cd openmemory/ui/docs-mintlify && mintlify dev` in another terminal.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ FAILURE: An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_test()
