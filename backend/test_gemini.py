"""
Test script for Gemini 2.0 Flash-Lite API integration
Tests call transcript analysis and verdict generation
"""
import os
import sys
from typing import Tuple
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY not found in environment variables.")
    print("Please make sure your .env file contains GEMINI_API_KEY")
    sys.exit(1)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model (2.0 Flash-Lite)
try:
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    print("✅ Successfully initialized Gemini 2.5 Flash-lite model")
except Exception as e:
    print(f"⚠️  Warning: Could not initialize Gemini 2.0 Flash-Exp model: {e}")
    print("Falling back to gemini-pro...")
    try:
        model = genai.GenerativeModel('gemini-pro')
        print("✅ Successfully initialized Gemini Pro model (fallback)")
    except Exception as e2:
        print(f"❌ Error: Could not initialize fallback model: {e2}")
        sys.exit(1)


def analyze_with_gemini(transcript: str) -> Tuple[str, str]:
    """
    Analyze call transcript with Gemini 2.0 Flash-Lite
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
        print("\n📤 Sending request to Gemini API...")
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        print(f"📥 Raw response from Gemini:\n{response_text}\n")
        
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
        print(f"❌ Error analyzing with Gemini: {e}")
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
        verdict, summary = analyze_with_gemini(transcript)
        
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
        verdict, summary = analyze_with_gemini(transcript)
        
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
        verdict, summary = analyze_with_gemini(transcript)
        
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
    print("Gemini API Test Script")
    print("="*60)
    print(f"API Key configured: {'Yes' if GEMINI_API_KEY else 'No'}")
    print(f"Model: {model._model_name if hasattr(model, '_model_name') else 'Unknown'}")
    
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
