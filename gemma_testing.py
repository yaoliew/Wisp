"""
Test script for Gemma local model integration via Ollama
Tests call transcript analysis and verdict generation
"""
import os
import sys
from typing import Tuple
from dotenv import load_dotenv
import ollama

# Load environment variables
load_dotenv()

# Environment variables
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Configure Ollama client
try:
    # Test connection to Ollama server
    ollama.list(host=OLLAMA_HOST)
    print(f"✅ Successfully connected to Ollama server at {OLLAMA_HOST}")
except Exception as e:
    print(f"❌ Error: Could not connect to Ollama server at {OLLAMA_HOST}")
    print(f"   Error: {e}")
    print("\n💡 Make sure Ollama is running:")
    print("   1. Install Ollama: https://ollama.ai")
    print("   2. Start Ollama server: ollama serve")
    print("   3. Pull Gemma model: ollama pull gemma3:1b")
    sys.exit(1)

# Verify model is available
model_available = False
try:
    models_response = ollama.list(host=OLLAMA_HOST)
    # Handle different response structures
    if isinstance(models_response, dict):
        models_list = models_response.get('models', [])
    else:
        models_list = models_response
    
    model_names = []
    for model in models_list:
        if isinstance(model, dict):
            model_names.append(model.get('name', ''))
        else:
            model_names.append(str(model))
    
    if OLLAMA_MODEL not in model_names:
        print(f"⚠️  Warning: Model '{OLLAMA_MODEL}' not found in Ollama.")
        print(f"   Available models: {', '.join(model_names) if model_names else 'None'}")
        print(f"\n💡 To install the model, run: ollama pull {OLLAMA_MODEL}")
        
        # Try to use first available gemma model as fallback
        gemma_models = [m for m in model_names if 'gemma' in m.lower()]
        if gemma_models:
            OLLAMA_MODEL = gemma_models[0]
            print(f"   Using fallback model: {OLLAMA_MODEL}")
            model_available = True
        else:
            print("❌ No Gemma models found. Please install one first.")
            sys.exit(1)
    else:
        print(f"✅ Model '{OLLAMA_MODEL}' is available")
        model_available = True
except Exception as e:
    print(f"⚠️  Warning: Could not verify model availability: {e}")
    print("   Continuing anyway...")


def analyze_with_gemma(transcript: str) -> Tuple[str, str]:
    """
    Analyze call transcript with Gemma via Ollama
    Returns: (verdict, 5-word_summary)
    """
    prompt = f"""You are a call screening AI. Analyze the following call transcript and determine if it's a SCAM or SAFE call.

Call Transcript:
{transcript}

Instructions:
1. Determine if this is a SCAM or SAFE call based on the caller's intent and behavior.
2. Provide a verdict: SCAM or SAFE
3. Provide a 5-word summary of the caller's intent (exactly 5 words, no more, no less).

Respond in this exact format:
VERDICT: [SCAM or SAFE]
SUMMARY: [exactly 5 words describing caller's intent]
"""

    try:
        print("\n📤 Sending request to Gemma via Ollama...")
        response = ollama.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            host=OLLAMA_HOST
        )
        # Handle response structure - could be dict or generator
        if isinstance(response, dict):
            response_text = response.get('response', '').strip()
        else:
            # If it's a generator (streaming), collect the response
            response_text = ''
            for chunk in response:
                if isinstance(chunk, dict):
                    response_text += chunk.get('response', '')
                else:
                    response_text += str(chunk)
            response_text = response_text.strip()
        
        print(f"📥 Raw response from Gemma:\n{response_text}\n")
        
        # Parse response
        verdict = None
        summary = None
        
        for line in response_text.split('\n'):
            if line.startswith('VERDICT:'):
                verdict_str = line.split(':', 1)[1].strip().upper()
                verdict = 'SCAM' if verdict_str == 'SCAM' else 'SAFE'
            elif line.startswith('SUMMARY:'):
                summary = line.split(':', 1)[1].strip()
        
        if not verdict or not summary:
            # Fallback parsing
            print("⚠️  Could not parse VERDICT/SUMMARY format, using fallback parsing...")
            if 'SCAM' in response_text.upper():
                verdict = 'SCAM'
            else:
                verdict = 'SAFE'
            
            # Extract summary (try to get 5 words)
            words = response_text.split()
            summary = ' '.join(words[:5]) if len(words) >= 5 else response_text[:50]
        
        # Ensure summary is exactly 5 words
        summary_words = summary.split()
        if len(summary_words) > 5:
            summary = ' '.join(summary_words[:5])
            print(f"⚠️  Summary was longer than 5 words, truncated to: {summary}")
        elif len(summary_words) < 5:
            # Pad with generic words if needed
            print(f"⚠️  Summary was shorter than 5 words, padding...")
            while len(summary_words) < 5:
                summary_words.append("call")
            summary = ' '.join(summary_words)
        
        return verdict, summary
        
    except Exception as e:
        print(f"❌ Error analyzing with Gemma: {e}")
        raise


def test_scam_call():
    """Test with a scam call transcript"""
    print("\n" + "="*60)
    print("TEST 1: SCAM Call Detection")
    print("="*60)
    
    transcript = """
    Hello, this is Microsoft Technical Support. We've detected a virus on your computer. 
    We need remote access to fix it immediately. Please provide your credit card information 
    to verify your identity. This is urgent - your computer will be permanently damaged if 
    you don't act now.
    """
    
    print(f"📝 Test Transcript:\n{transcript.strip()}\n")
    
    try:
        verdict, summary = analyze_with_gemma(transcript)
        
        print("\n" + "-"*60)
        print("RESULTS:")
        print("-"*60)
        print(f"Verdict: {verdict}")
        print(f"Summary: {summary}")
        print(f"Summary word count: {len(summary.split())}")
        
        if verdict == "SCAM":
            print("✅ Correctly identified as SCAM")
        else:
            print("⚠️  Expected SCAM but got SAFE")
            
        if len(summary.split()) == 5:
            print("✅ Summary is exactly 5 words")
        else:
            print(f"⚠️  Summary should be 5 words but is {len(summary.split())}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")


def test_safe_call():
    """Test with a safe call transcript"""
    print("\n" + "="*60)
    print("TEST 2: SAFE Call Detection")
    print("="*60)
    
    transcript = """
    Hi, this is Sarah from your dentist's office. I'm calling to confirm your appointment 
    tomorrow at 2 PM. We just wanted to make sure you're still able to make it. 
    If you need to reschedule, please call us back at 555-1234. Thanks!
    """
    
    print(f"📝 Test Transcript:\n{transcript.strip()}\n")
    
    try:
        verdict, summary = analyze_with_gemma(transcript)
        
        print("\n" + "-"*60)
        print("RESULTS:")
        print("-"*60)
        print(f"Verdict: {verdict}")
        print(f"Summary: {summary}")
        print(f"Summary word count: {len(summary.split())}")
        
        if verdict == "SAFE":
            print("✅ Correctly identified as SAFE")
        else:
            print("⚠️  Expected SAFE but got SCAM")
            
        if len(summary.split()) == 5:
            print("✅ Summary is exactly 5 words")
        else:
            print(f"⚠️  Summary should be 5 words but is {len(summary.split())}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")


def test_custom_transcript():
    """Test with a custom transcript from command line"""
    if len(sys.argv) > 1:
        transcript = " ".join(sys.argv[1:])
    else:
        print("\nEnter a call transcript to test (or press Enter to skip):")
        transcript = input().strip()
        if not transcript:
            return
    
    print("\n" + "="*60)
    print("TEST 3: Custom Transcript")
    print("="*60)
    print(f"📝 Test Transcript:\n{transcript}\n")
    
    try:
        verdict, summary = analyze_with_gemma(transcript)
        
        print("\n" + "-"*60)
        print("RESULTS:")
        print("-"*60)
        print(f"Verdict: {verdict}")
        print(f"Summary: {summary}")
        print(f"Summary word count: {len(summary.split())}")
        
        if len(summary.split()) == 5:
            print("✅ Summary is exactly 5 words")
        else:
            print(f"⚠️  Summary should be 5 words but is {len(summary.split())}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")


def main():
    """Run all tests"""
    print("="*60)
    print("Gemma Ollama Test Script")
    print("="*60)
    print(f"Ollama Host: {OLLAMA_HOST}")
    print(f"Model: {OLLAMA_MODEL}")
    
    # Run standard tests
    test_scam_call()
    test_safe_call()
    
    # Run custom test if provided
    test_custom_transcript()
    
    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)


if __name__ == "__main__":
    main()
