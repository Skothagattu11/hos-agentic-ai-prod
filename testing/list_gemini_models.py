"""
Quick script to list available Gemini models
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    print("ERROR: GEMINI_API_KEY not set")
    exit(1)

genai.configure(api_key=gemini_api_key)

print("Available Gemini models:")
print("="*80)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"Model: {model.name}")
        print(f"  Display name: {model.display_name}")
        print(f"  Description: {model.description}")
        print()
