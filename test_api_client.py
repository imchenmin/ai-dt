#!/usr/bin/env python3
"""
Test script for the AI-DT LLM API server
"""

import requests
import json
import time


def test_api_server(base_url: str = "http://localhost:8000"):
    """Test the API server functionality"""
    
    print(f"Testing API server at {base_url}")
    
    # Test 1: Root endpoint
    print("\n1. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: List models
    print("\n2. Testing models endpoint...")
    try:
        response = requests.get(f"{base_url}/v1/models")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Available models: {len(data.get('data', []))}")
        for model in data.get('data', []):
            print(f"  - {model.get('id')} (owned by {model.get('owned_by')})")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Chat completions
    print("\n3. Testing chat completions...")
    try:
        chat_request = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Write a simple hello world function in C."}
            ],
            "max_tokens": 150,
            "temperature": 0.3
        }
        
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json=chat_request
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Model: {data.get('model')}")
            print(f"Response: {data['choices'][0]['message']['content'][:100]}...")
            if data.get('usage'):
                usage = data['usage']
                print(f"Token usage: {usage['prompt_tokens']} + {usage['completion_tokens']} = {usage['total_tokens']}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Text completions
    print("\n4. Testing text completions...")
    try:
        completion_request = {
            "model": "gpt-3.5-turbo",
            "prompt": "Write a simple C function that adds two numbers:",
            "max_tokens": 100,
            "temperature": 0.3
        }
        
        response = requests.post(
            f"{base_url}/v1/completions",
            headers={"Content-Type": "application/json"},
            json=completion_request
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Model: {data.get('model')}")
            print(f"Response: {data['choices'][0]['text'][:100]}...")
            if data.get('usage'):
                usage = data['usage']
                print(f"Token usage: {usage['prompt_tokens']} + {usage['completion_tokens']} = {usage['total_tokens']}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")


def test_openai_compatibility():
    """Test OpenAI client compatibility"""
    print("\n5. Testing OpenAI client compatibility...")
    
    try:
        # This would work if openai package is installed
        # from openai import OpenAI
        # 
        # client = OpenAI(
        #     api_key="dummy-key",  # Not needed for local server
        #     base_url="http://localhost:8000/v1"
        # )
        # 
        # response = client.chat.completions.create(
        #     model="gpt-3.5-turbo",
        #     messages=[
        #         {"role": "user", "content": "Hello, world!"}
        #     ]
        # )
        # 
        # print(f"OpenAI client response: {response.choices[0].message.content}")
        
        print("OpenAI client compatibility test skipped (requires openai package)")
        print("To test with OpenAI client, install: pip install openai")
        print("Then uncomment the code in this function")
        
    except ImportError:
        print("OpenAI package not installed. Install with: pip install openai")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test AI-DT LLM API server")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="API server URL (default: http://localhost:8000)")
    parser.add_argument("--wait", type=int, default=2,
                       help="Wait time before starting tests (default: 2 seconds)")
    
    args = parser.parse_args()
    
    if args.wait > 0:
        print(f"Waiting {args.wait} seconds for server to start...")
        time.sleep(args.wait)
    
    test_api_server(args.url)
    test_openai_compatibility()
    
    print("\nAPI testing completed!")