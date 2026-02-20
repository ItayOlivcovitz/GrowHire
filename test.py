import os
import openai
from dotenv import load_dotenv

# Try to import google.generativeai, handle if not installed
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("[WARNING] google-generativeai not installed. Gemini tests will be skipped.")
    print("          Install with: pip install google-generativeai")
    print()

# Load environment variables from .env file
load_dotenv()

def test_openai_key():
    """Test the OpenAI API key by making a simple request."""
    
    print("=" * 60)
    print("Testing OpenAI API Key")
    print("=" * 60)
    
    # Get the API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found in .env file")
        return False
    
    # Show first and last few characters of the key (for security)
    masked_key = f"{api_key[:10]}...{api_key[-10:]}" if len(api_key) > 20 else "***"
    print(f"[OK] API Key found: {masked_key}")
    print(f"     Key length: {len(api_key)} characters")
    print()
    
    # Set the API key
    openai.api_key = api_key
    
    # Make a simple test request
    print("[INFO] Making test request to OpenAI...")
    print()
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, API test successful!' if you can read this."}
            ],
            max_tokens=50
        )
        
        # Extract the response
        if "choices" in response and response["choices"]:
            response_text = response["choices"][0].get("message", {}).get("content", "").strip()
            
            if response_text:
                print("[SUCCESS] OpenAI API is working correctly!")
                print(f"         Response: {response_text}")
                print()
                return True
            else:
                print("[ERROR] Response was empty")
                return False
        else:
            print("[ERROR] Invalid response structure")
            print(f"        Response: {response}")
            return False
            
    except openai.error.AuthenticationError as e:
        print("[ERROR] AUTHENTICATION ERROR: Invalid API key")
        print(f"        Details: {e}")
        print()
        print("[TIP] Possible issues:")
        print("      - API key is incorrect or expired")
        print("      - API key format is wrong")
        print("      - API key doesn't have proper permissions")
        return False
        
    except openai.error.RateLimitError as e:
        print("[ERROR] RATE LIMIT ERROR: Too many requests")
        print(f"        Details: {e}")
        return False
        
    except openai.error.APIError as e:
        print("[ERROR] API ERROR: OpenAI API returned an error")
        print(f"        Details: {e}")
        return False
        
    except Exception as e:
        print(f"[ERROR] UNEXPECTED ERROR: {type(e).__name__}")
        print(f"        Details: {e}")
        print()
        print("[TIP] This might be a compatibility issue with the openai library version.")
        print(f"      Current version: {openai.__version__}")
        return False

def test_gemini_key():
    """Test the Gemini API key by making a simple request."""
    
    print("=" * 60)
    print("Testing Gemini API Key")
    print("=" * 60)
    
    if not GEMINI_AVAILABLE:
        print("[SKIP] google-generativeai module is not installed.")
        print("       Install with: pip install google-generativeai")
        return False
    
    # Get the API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("[ERROR] GEMINI_API_KEY not found in .env file")
        return False
    
    # Show first and last few characters of the key (for security)
    masked_key = f"{api_key[:10]}...{api_key[-10:]}" if len(api_key) > 20 else "***"
    print(f"[OK] API Key found: {masked_key}")
    print(f"     Key length: {len(api_key)} characters")
    print()
    
    # Configure the API key
    genai.configure(api_key=api_key)
    
    # Make a simple test request
    print("[INFO] Making test request to Gemini...")
    print()
    
    try:
        # List available models to find one that works
        print("[INFO] Checking available models...")
        try:
            models = genai.list_models()
            available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            print(f"[INFO] Found {len(available_models)} available models")
            if available_models:
                # Use the first available model
                model_name = available_models[0].split('/')[-1]  # Extract just the model name
                print(f"[INFO] Using model: {model_name}")
                model = genai.GenerativeModel(model_name)
            else:
                # Fallback: try common model names
                print("[INFO] No models found via list_models, trying common names...")
                model = genai.GenerativeModel("models/gemini-pro")
        except Exception as list_error:
            print(f"[INFO] Could not list models: {list_error}")
            print("[INFO] Trying default model: models/gemini-pro")
            # Try with "models/" prefix
            model = genai.GenerativeModel("models/gemini-pro")
        
        # Generate content with the prompt
        response = model.generate_content(
            "Say 'Hello, API test successful!' if you can read this.",
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=50
            )
        )
        
        # Extract the response text
        if response and response.text:
            response_text = response.text.strip()
            print("[SUCCESS] Gemini API is working correctly!")
            print(f"         Response: {response_text}")
            print()
            return True
        else:
            print("[ERROR] Response was empty or invalid")
            return False
            
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        print(f"[ERROR] UNEXPECTED ERROR: {error_type}")
        print(f"        Details: {error_msg}")
        print()
        
        # Provide helpful tips based on common errors
        if "API_KEY" in error_msg.upper() or "AUTHENTICATION" in error_msg.upper():
            print("[TIP] Possible issues:")
            print("      - API key is incorrect or expired")
            print("      - API key format is wrong")
            print("      - API key doesn't have proper permissions")
        elif "QUOTA" in error_msg.upper() or "RATE" in error_msg.upper():
            print("[TIP] Rate limit or quota exceeded.")
            print("      - Check your Google AI Studio quota")
            print("      - Wait a few minutes and try again")
        else:
            print("[TIP] Check that google-generativeai is installed:")
            print("      pip install google-generativeai")
        
        return False

if __name__ == "__main__":
    print("\n")
    print("=" * 60)
    print("API Connection Tests")
    print("=" * 60)
    print("\n")
    
    # Test OpenAI
    openai_success = test_openai_key()
    print("\n")
    
    # Test Gemini
    gemini_success = test_gemini_key()
    print("\n")
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"OpenAI API: {'[PASS]' if openai_success else '[FAIL]'}")
    print(f"Gemini API: {'[PASS]' if gemini_success else '[FAIL]'}")
    print("=" * 60)
