import requests
import time
import json

def test_chat():
    url = "https://hull-chat--example-llm-model-chat.modal.run"
    payload = {"prompt": "What is the difference between formative and summative assessment?"}
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
            # print("\nFull Response:")
            # print(json.dumps(result, indent=2))
            
            if "response" in result:
                print("\nGenerated Text:")
                print("==============")
                print(result["response"].strip())
            else:
                print("\nNo response text in result")
                print("Raw result:", result)
        else:
            print("\nError:")
            print(response.text)
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        if hasattr(e, 'response'):
            print("Response content:", e.response.content)

if __name__ == "__main__":
    test_chat()