"""
Test script for Mistral 7B via Ollama.

This script tests:
1. Basic inference
2. Response latency
3. Function calling (tool use)
4. System prompts

Usage:
    python scripts/test_mistral_ollama.py
"""

import time
import ollama

def test_basic_inference():
    """Test basic question/response."""
    print("=" * 60)
    print("Step 1: Testing Basic Inference")
    print("=" * 60)
    
    response = ollama.chat(model='mistral', messages=[
        {'role': 'user', 'content': 'What is 2 + 2?'}
    ])
    
    print(f"Response: {response['message']['content']}")
    return response

def test_latency():
    """Measure response time."""
    print("\n" + "=" * 60)
    print("Step 2: Testing Latency")
    print("=" * 60)
    
    start = time.time()
    response = ollama.chat(model='mistral', messages=[
        {'role': 'user', 'content': 'Say hello'}
    ])
    elapsed = time.time() - start
    
    print(f"Response time: {elapsed:.2f}s")
    print(f"Response: {response['message']['content']}")
    return elapsed

def test_system_prompt():
    """Test setting a system prompt to control AI behavior."""
    print("\n" + "=" * 60)
    print("Step 3: Testing System Prompt")
    print("=" * 60)
    
    response = ollama.chat(model='mistral', messages=[
        {'role': 'system', 'content': 'You are a helpful voice assistant for scheduling meetings. Be concise and friendly.'},
        {'role': 'user', 'content': 'I want to schedule a meeting tomorrow at 2pm'}
    ])
    
    print(f"Response: {response['message']['content']}")
    return response


def test_function_calling():
    """Test if the model can call tools/functions."""
    print("\n" + "=" * 60)
    print("Step 4: Testing Function Calling")
    print("=" * 60)
    
    # Define available tools
    tools = [
        {
            'type': 'function',
            'function': {
                'name': 'create_calendar_event',
                'description': 'Create a calendar event',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'title': {'type': 'string', 'description': 'Meeting title'},
                        'date': {'type': 'string', 'description': 'Date (YYYY-MM-DD)'},
                        'time': {'type': 'string', 'description': 'Time (HH:MM)'}
                    },
                    'required': ['title', 'date', 'time']
                }
            }
        }
    ]
    
    response = ollama.chat(
        model='mistral',
        messages=[
            {'role': 'user', 'content': 'Schedule a team meeting for tomorrow at 2pm'}
        ],
        tools=tools
    )
    
    print(f"Response: {response['message']['content']}")
    
    # Check if the model called a tool
    if 'tool_calls' in response['message']:
        print("✓ Model called a tool!")
        for tool_call in response['message']['tool_calls']:
            print(f"  Tool: {tool_call['function']['name']}")
            print(f"  Arguments: {tool_call['function']['arguments']}")
    else:
        print("⚠ Model did not call a tool (may need different model or prompt)")
    
    return response

def main():
    """Run all tests."""
    print("Mistral 7B via Ollama Test Suite")
    print("=" * 60)
    
    test_basic_inference()
    test_latency()
    test_system_prompt()
    test_function_calling()
    
    print("\n" + "=" * 60)
    print("Tests Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()