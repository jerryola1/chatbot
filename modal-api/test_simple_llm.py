import requests
import time
import json

def test_chat(prompt: str):
    url = "https://hull-chat--example-llm-model-chat.modal.run"
    payload = {"prompt": prompt}
    headers = {"Content-Type": "application/json"}
    
    print("\nTesting LLM Endpoint")
    print("===================")
    print(f"URL: {url}")
    print(f"Prompt: {payload['prompt']}")
    
    try:
        print("\nSending request...")
        start = time.time()
        response = requests.post(url, json=payload, headers=headers)
        duration = time.time() - start
        
        print(f"\nRequest completed in {duration:.1f} seconds")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\nComplete Response:")
            print("=================")
            print(json.dumps(result, indent=2))
        else:
            print("\nError:")
            print(response.text)
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        if hasattr(e, 'response'):
            print("Response content:", e.response.content)

def run_test_suite():
    # Test 1: Common query (should have high confidence)
    print("\n=== Test 1: Common Query ===")
    test_chat("What are the library opening hours?")
    
    time.sleep(2)
    
    # Test 2: Specific query (should have lower confidence)
    print("\n=== Test 2: Specific Query ===")
    test_chat("What specific research equipment is available in the chemistry department?")
    
    time.sleep(2)
    
    # Test 3: Very specific query (should have low confidence)
    print("\n=== Test 3: Very Specific Query ===")
    test_chat("What are the opening hours for the Allam Medical Building's simulation suite?")

if __name__ == "__main__":
    run_test_suite()