"""
Call screening evaluation module
Handles Gemini-based call transcript analysis
"""
import os
import logging
from typing import Tuple
from dotenv import load_dotenv
import google.generativeai as genai
from enum import Enum

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not configured")


class Verdict(str, Enum):
    """Call verdict types"""
    SCAM = "SCAM"
    SAFE = "SAFE"


# Initialize Gemini model (2.0 Flash-Lite)
model = None
if GEMINI_API_KEY:
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("Successfully initialized Gemini 2.0 Flash-Exp model")
    except Exception as e:
        logger.warning(f"Could not initialize Gemini model: {e}. Using fallback model.")
        try:
            model = genai.GenerativeModel('gemini-pro')
            logger.info("Using Gemini Pro fallback model")
        except Exception as e2:
            logger.error(f"Could not initialize fallback model: {e2}")


async def analyze_with_gemini(transcript: str) -> Tuple[Verdict, str]:
    """
    Analyze call transcript with Gemini 2.0 Flash-Lite
    Returns: (verdict, 5-word_summary)
    """
    if not model:
        logger.error("Gemini model not initialized")
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
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
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
        
        logger.info(f"Gemini verdict: {verdict}, Summary: {summary}")
        return verdict, summary
        
    except Exception as e:
        logger.error(f"Error analyzing with Gemini: {e}")
        # Default to SAFE if analysis fails
        return Verdict.SAFE, "Unable to analyze call transcript"
