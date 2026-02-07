"""
Wisp - AI-first call-screening service backend
FastAPI backend for screening calls using Gemini 2.0 Flash-Lite
"""
import os
import logging
from typing import Dict, Any, Optional, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import google.generativeai as genai
import httpx
from enum import Enum

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Wisp Call Screening API", version="1.0.0")

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RETELL_API_KEY = os.getenv("RETELL_API_KEY")
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
MESSAGE_PROFILE_ID = os.getenv("MESSAGE_PROFILE_ID")
WISP_PHONE = "+14702282477"

# Validate required environment variables
if not all([GEMINI_API_KEY, RETELL_API_KEY, TELNYX_API_KEY, MESSAGE_PROFILE_ID]):
    logger.warning("Missing required environment variables. Please check your .env file.")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model (2.0 Flash-Lite)
try:
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
except Exception as e:
    logger.warning(f"Could not initialize Gemini model: {e}. Using fallback model.")
    model = genai.GenerativeModel('gemini-pro')


class Verdict(str, Enum):
    """Call verdict types"""
    SCAM = "SCAM"
    SAFE = "SAFE"


class ScreeningRequest(BaseModel):
    """Request model for call screening"""
    call_id: str = Field(..., description="Unique call identifier from Retell")
    transcript: str = Field(..., description="Call transcript to analyze")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional call metadata")


class ScreeningResponse(BaseModel):
    """Response model for call screening"""
    verdict: Verdict = Field(..., description="SCAM or SAFE verdict")
    summary: str = Field(..., description="5-word summary of caller's intent")
    call_id: str = Field(..., description="Call identifier")


async def analyze_with_gemini(transcript: str) -> Tuple[Verdict, str]:
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


async def terminate_retell_call(call_id: str) -> bool:
    """Terminate a call via Retell AI API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.retellai.com/update-call/{call_id}",
                headers={
                    "Authorization": f"Bearer {RETELL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={"end_call": True},
                timeout=10.0
            )
            response.raise_for_status()
            logger.info(f"Successfully terminated call {call_id}")
            return True
    except Exception as e:
        logger.error(f"Error terminating Retell call: {e}")
        return False


async def warm_transfer_retell_call(call_id: str, target_number: str, whisper_message: str) -> bool:
    """Initiate warm transfer via Retell AI API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.retellai.com/update-call/{call_id}",
                headers={
                    "Authorization": f"Bearer {RETELL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "transfer_phone_number": target_number,
                    "enable_voicemail_detection": False,
                    "whisper_message": whisper_message
                },
                timeout=10.0
            )
            response.raise_for_status()
            logger.info(f"Successfully initiated warm transfer for call {call_id}")
            return True
    except Exception as e:
        logger.error(f"Error initiating warm transfer: {e}")
        return False


async def send_telnyx_sms(to_number: str, message: str) -> bool:
    """Send SMS via Telnyx API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.telnyx.com/v2/messages",
                headers={
                    "Authorization": f"Bearer {TELNYX_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": WISP_PHONE,
                    "to": to_number,
                    "text": message,
                    "messaging_profile_id": MESSAGE_PROFILE_ID
                },
                timeout=10.0
            )
            response.raise_for_status()
            logger.info(f"Successfully sent SMS to {to_number}")
            return True
    except Exception as e:
        logger.error(f"Error sending Telnyx SMS: {e}")
        return False


@app.post("/wisp-screen", response_model=ScreeningResponse)
async def wisp_screen(request: ScreeningRequest):
    """
    Main screening endpoint for Wisp call screening service.
    
    Analyzes call transcript with Gemini 2.0 Flash-Lite and executes
    appropriate actions based on verdict (SCAM or SAFE).
    """
    logger.info(f"Received screening request for call {request.call_id}")
    
    # Step 1: Analyze transcript with Gemini
    verdict, summary = await analyze_with_gemini(request.transcript)
    
    # Step 2: Execute based on verdict
    if verdict == Verdict.SCAM:
        # SCAM flow: Terminate call + Send SMS alert
        logger.info(f"SCAM detected for call {request.call_id}. Terminating call and sending alert.")
        
        # Terminate call via Retell
        await terminate_retell_call(request.call_id)
        
        # Send SMS alert
        sms_message = f"🚨 Wisp Blocked: {summary}."
        await send_telnyx_sms(WISP_PHONE, sms_message)
        
    else:  # SAFE
        # SAFE flow: Warm transfer + Whisper + SMS alert
        logger.info(f"SAFE call detected for call {request.call_id}. Initiating warm transfer.")
        
        # Create whisper message
        whisper_message = f"Wisp here. Verified: {summary}. Press any key to bridge."
        
        # Initiate warm transfer via Retell
        await warm_transfer_retell_call(request.call_id, WISP_PHONE, whisper_message)
        
        # Send SMS alert
        sms_message = f"✅ Wisp Verified: {summary}. Ringing you now."
        await send_telnyx_sms(WISP_PHONE, sms_message)
    
    return ScreeningResponse(
        verdict=verdict,
        summary=summary,
        call_id=request.call_id
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Wisp Call Screening API",
        "gemini_configured": GEMINI_API_KEY is not None,
        "retell_configured": RETELL_API_KEY is not None,
        "telnyx_configured": TELNYX_API_KEY is not None
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Wisp Call Screening API",
        "version": "1.0.0",
        "endpoints": {
            "screening": "/wisp-screen",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
