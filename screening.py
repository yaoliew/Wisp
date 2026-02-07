"""
Call screening evaluation module
Handles Gemma-based call transcript analysis via Ollama
"""
import os
import sys
import asyncio
import logging
from typing import Tuple
from dotenv import load_dotenv
from enum import Enum

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Environment variables
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Set OLLAMA_HOST environment variable for the ollama library
if OLLAMA_HOST != "http://localhost:11434":
    os.environ["OLLAMA_HOST"] = OLLAMA_HOST

# Import ollama
try:
    import ollama
    logger.info("Ollama library imported successfully")
except ImportError as e:
    logger.error(f"Could not import ollama package: {e}")
    logger.error("Please install it: pip install ollama")
    ollama = None


class Verdict(str, Enum):
    """Call verdict types"""
    SCAM = "SCAM"
    SAFE = "SAFE"


# Verify Ollama connection and model availability
def _check_ollama_connection():
    """Check if Ollama is available and model exists"""
    if not ollama:
        return False
    try:
        ollama.list()
        return True
    except Exception as e:
        logger.warning(f"Could not connect to Ollama: {e}")
        return False


async def analyze_with_gemini(transcript: str) -> Tuple[Verdict, str]:
    """
    Analyze call transcript with Gemma3:1b via Ollama
    Returns: (verdict, 5-word_summary)
    
    Note: Function name kept as analyze_with_gemini for backward compatibility
    """
    if not ollama:
        logger.error("Ollama library not available")
        return Verdict.SAFE, "Unable to analyze call transcript"
    
    if not _check_ollama_connection():
        logger.error("Ollama server not available")
        return Verdict.SAFE, "Unable to analyze call transcript"
    
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
        response = ollama.generate(
            model=OLLAMA_MODEL,
            prompt=prompt
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
        
        # Parse response
        verdict = None
        summary = None
        
        for line in response_text.split('\n'):
            if line.startswith('VERDICT:'):
                verdict_str = line.split(':', 1)[1].strip().upper()
                verdict = Verdict.SCAM if verdict_str == 'SCAM' else Verdict.SAFE
            elif line.startswith('SUMMARY:'):
                summary = line.split(':', 1)[1].strip()
        
        if not verdict or not summary:
            # Fallback parsing
            if 'SCAM' in response_text.upper():
                verdict = Verdict.SCAM
            else:
                verdict = Verdict.SAFE
            
            # Extract summary (try to get 5 words)
            words = response_text.split()
            summary = ' '.join(words[:5]) if len(words) >= 5 else response_text[:50]
        
        # Ensure summary is exactly 5 words
        summary_words = summary.split()
        if len(summary_words) > 5:
            summary = ' '.join(summary_words[:5])
        elif len(summary_words) < 5:
            # Pad with generic words if needed
            while len(summary_words) < 5:
                summary_words.append("call")
            summary = ' '.join(summary_words)
        
        logger.info(f"Gemma verdict: {verdict}, Summary: {summary}")
        return verdict, summary
        
    except Exception as e:
        logger.error(f"Error analyzing with Gemma: {e}")
        # Default to SAFE if analysis fails
        return Verdict.SAFE, "Unable to analyze call transcript"


async def main():
    """Main function to call analyze_with_gemini directly from command line"""
    # Configure logging for console output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("="*60)
    print("Wisp Call Screening - Direct Analysis")
    print("="*60)
    print(f"Ollama Host: {OLLAMA_HOST}")
    print(f"Model: {OLLAMA_MODEL}")
    print()
    
    # Get transcript from command line arguments or prompt
    if len(sys.argv) > 1:
        transcript = " ".join(sys.argv[1:])
    else:
        print("Enter a call transcript to analyze (or press Enter to use example):")
        transcript = input().strip()
        if not transcript:
            # Use example transcript
            transcript = """
            Hello, this is Microsoft Technical Support. We've detected a virus on your computer. 
            We need remote access to fix it immediately. Please provide your credit card information 
            to verify your identity. This is urgent - your computer will be permanently damaged if 
            you don't act now.
            """
            print("\nUsing example transcript (Microsoft tech support scam)...")
    
    print("\n" + "="*60)
    print("Analyzing Transcript")
    print("="*60)
    print(f"📝 Transcript:\n{transcript.strip()}\n")
    
    try:
        verdict, summary = await analyze_with_gemini(transcript)
        
        print("\n" + "-"*60)
        print("RESULTS:")
        print("-"*60)
        print(f"Verdict: {verdict.value}")
        print(f"Summary: {summary}")
        print(f"Summary word count: {len(summary.split())}")
        
        if len(summary.split()) == 5:
            print("✅ Summary is exactly 5 words")
        else:
            print(f"⚠️  Summary should be 5 words but is {len(summary.split())}")
        
        print("\n" + "="*60)
        print("Analysis Complete!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.exception("Error in main function")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
