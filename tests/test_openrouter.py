#!/usr/bin/env python3
"""
Test script for OpenRouter client setup.
Run this to verify your OpenRouter API key is working.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from app.ai.client import OpenRouterClient

def test_openrouter_client():
    """Test the OpenRouter client with a simple prompt."""
    try:
        client = OpenRouterClient()
        print("✅ OpenRouter client initialized successfully")

        # Test with a simple prompt
        test_prompt = "Say 'Hello, OpenRouter is working!' and nothing else."
        response = client.generate(test_prompt)
        print(f"Response: {response}")

        # Try to parse as JSON
        import json
        try:
            parsed = json.loads(response)
            print("✅ Response is valid JSON")
        except json.JSONDecodeError:
            print("⚠️  Response is not JSON, but that's okay for testing")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Make sure OPENROUTER_API_KEY is set in your .env file")
    except Exception as e:
        print(f"❌ API error: {e}")

if __name__ == "__main__":
    test_openrouter_client()