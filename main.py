"""
Wisp - AI-first call-screening service backend
Fully Retell-native FastAPI backend for screening calls using Gemini 2.5 Flash-Lite
Integrates with Retell AI for call orchestration and webhooks
"""
import os
import logging
import hmac
import hashlib
import asyncio
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import httpx
from datetime import datetime
from screening import analyze_with_gemini, Verdict

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Wisp Call Screening API", version="1.0.0")

# Call state management (in-memory store for active calls)
active_calls: Dict[str, Dict[str, Any]] = {}

# Environment variables
RETELL_API_KEY = os.getenv("RETELL_API_KEY")
RETELL_WEBHOOK_SECRET = os.getenv("RETELL_WEBHOOK_SECRET")
WISP_PHONE = "+14702282477"

# Validate required environment variables
if not RETELL_API_KEY:
    logger.warning("Missing required environment variables. Please check your .env file.")


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


class RetellWebhookEvent(BaseModel):
    """Retell webhook event model"""
    event: str = Field(..., description="Event type (call_started, call_ended, etc.)")
    call: Dict[str, Any] = Field(..., description="Call information")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional event data")


def verify_retell_webhook(payload: bytes, signature: str) -> bool:
    """Verify Retell webhook signature"""
    if not RETELL_WEBHOOK_SECRET:
        logger.warning("RETELL_WEBHOOK_SECRET not configured, skipping webhook verification")
        return True
    
    try:
        # Retell signature format: "v=<timestamp>,d=<signature>"
        # Extract the signature part (after "d=")
        if "," in signature:
            parts = signature.split(",")
            sig_part = None
            for part in parts:
                if part.startswith("d="):
                    sig_part = part[2:]  # Remove "d=" prefix
                    break
            if not sig_part:
                return False
            signature = sig_part
        
        # Compute expected signature
        expected_signature = hmac.new(
            RETELL_WEBHOOK_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


async def terminate_retell_call(call_id: str, retry_count: int = 3) -> bool:
    """Terminate a call via Retell AI API with retry logic"""
    for attempt in range(retry_count):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.retellai.com/update-call/{call_id}",
                    headers={
                        "Authorization": f"Bearer {RETELL_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "end_call": True
                        "end_call_message": "This call has been blocked. Please remove this number from your call list. Goodbye."
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Successfully terminated call {call_id}")
                
                # Update call state
                if call_id in active_calls:
                    active_calls[call_id]["status"] = "terminated"
                    active_calls[call_id]["terminated_at"] = datetime.utcnow().isoformat()
                
                return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Call {call_id} not found, may have already ended")
                return True  # Consider this success if call doesn't exist
            if attempt < retry_count - 1:
                logger.warning(f"Error terminating call {call_id} (attempt {attempt + 1}/{retry_count}): {e}")
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"Error terminating Retell call after {retry_count} attempts: {e}")
                return False
        except Exception as e:
            if attempt < retry_count - 1:
                logger.warning(f"Error terminating call {call_id} (attempt {attempt + 1}/{retry_count}): {e}")
                await asyncio.sleep(1 * (attempt + 1))
            else:
                logger.error(f"Error terminating Retell call after {retry_count} attempts: {e}")
                return False
    return False


async def warm_transfer_retell_call(call_id: str, target_number: str, whisper_message: str, retry_count: int = 3) -> bool:
    """Initiate warm transfer via Retell AI API with retry logic"""
    for attempt in range(retry_count):
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
                logger.info(f"Successfully initiated warm transfer for call {call_id} to {target_number}")
                
                # Update call state
                if call_id in active_calls:
                    active_calls[call_id]["transfer_initiated"] = True
                    active_calls[call_id]["transfer_target"] = target_number
                    active_calls[call_id]["transfer_initiated_at"] = datetime.utcnow().isoformat()
                
                return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Call {call_id} not found, cannot transfer")
                return False
            if attempt < retry_count - 1:
                logger.warning(f"Error initiating transfer for call {call_id} (attempt {attempt + 1}/{retry_count}): {e}")
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"Error initiating warm transfer after {retry_count} attempts: {e}")
                return False
        except Exception as e:
            if attempt < retry_count - 1:
                logger.warning(f"Error initiating transfer for call {call_id} (attempt {attempt + 1}/{retry_count}): {e}")
                await asyncio.sleep(1 * (attempt + 1))
            else:
                logger.error(f"Error initiating warm transfer after {retry_count} attempts: {e}")
                return False
    return False


@app.post("/wisp-screen", response_model=ScreeningResponse)
async def wisp_screen(request: ScreeningRequest):
    """
    Main screening endpoint for Wisp call screening service.
    
    Analyzes call transcript with Gemini 2.0 Flash-Lite and executes
    appropriate actions based on verdict (SCAM or SAFE).
    Works with both Custom Tool calls and webhook-driven flows.
    """
    logger.info(f"Received screening request for call {request.call_id}")
    
    # Check if call is in active calls (from webhook)
    call_state = active_calls.get(request.call_id, {})
    
    # Step 1: Analyze transcript with Gemini
    verdict, summary = await analyze_with_gemini(request.transcript)
    
    # Update call state with screening result
    if request.call_id in active_calls:
        active_calls[request.call_id]["screening_verdict"] = verdict.value
        active_calls[request.call_id]["screening_summary"] = summary
        active_calls[request.call_id]["screened_at"] = datetime.utcnow().isoformat()
    
    # Step 2: Execute based on verdict
    if verdict == Verdict.SCAM:
        # SCAM flow: Terminate call
        logger.info(f"SCAM detected for call {request.call_id}. Terminating call.")
        
        # Terminate call via Retell (with retry logic)
        termination_success = await terminate_retell_call(request.call_id)
        if not termination_success:
            logger.error(f"Failed to terminate call {request.call_id}")
        
    else:  # SAFE
        # SAFE flow: Warm transfer + Whisper
        logger.info(f"SAFE call detected for call {request.call_id}. Initiating warm transfer.")
        
        # Create whisper message
        whisper_message = f"Wisp here. Verified: {summary}. Press any key to bridge."
        
        # Initiate warm transfer via Retell (with retry logic)
        transfer_success = await warm_transfer_retell_call(request.call_id, WISP_PHONE, whisper_message)
        if not transfer_success:
            logger.error(f"Failed to initiate warm transfer for call {request.call_id}")
    
    return ScreeningResponse(
        verdict=verdict,
        summary=summary,
        call_id=request.call_id
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from screening import GEMINI_API_KEY
    return {
        "status": "healthy",
        "service": "Wisp Call Screening API",
        "gemini_configured": GEMINI_API_KEY is not None,
        "retell_configured": RETELL_API_KEY is not None
    }


@app.post("/retell-webhook")
async def retell_webhook(
    request: Request,
    x_retell_signature: Optional[str] = Header(None, alias="X-Retell-Signature")
):
    """
    Retell webhook endpoint for call event handling.
    Handles call_started, call_ended, call_transferred events.
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify webhook signature if secret is configured
        # Note: For development/testing, signature verification failures are logged but don't block requests
        # In production, you should enable strict verification
        if RETELL_WEBHOOK_SECRET and x_retell_signature:
            if not verify_retell_webhook(body, x_retell_signature):
                logger.warning("Invalid webhook signature, but allowing request (development mode)")
                # In production, uncomment the line below to reject invalid signatures:
                # raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse webhook payload from body (already read, can't use request.json())
        try:
            body_str = body.decode('utf-8')
            payload = json.loads(body_str)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(e)}")
        except UnicodeDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid body encoding: {str(e)}")
        event_type = payload.get("event")
        call_data = payload.get("call", {})
        call_id = call_data.get("call_id")
        
        logger.info(f"Received Retell webhook: {event_type} for call {call_id}")
        
        # Handle different event types
        if event_type == "call_started":
            # Store call state
            active_calls[call_id] = {
                "call_id": call_id,
                "from_number": call_data.get("from_number"),
                "to_number": call_data.get("to_number"),
                "started_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            logger.info(f"Call {call_id} started, stored in active calls")
            
        elif event_type == "call_ended":
            # Remove from active calls
            if call_id in active_calls:
                active_calls[call_id]["status"] = "ended"
                active_calls[call_id]["ended_at"] = datetime.utcnow().isoformat()
                # Keep for a short time for analytics, then remove
                # In production, you might want to persist this to a database
            logger.info(f"Call {call_id} ended")
            
        elif event_type == "call_transferred":
            # Update call state with transfer information
            if call_id in active_calls:
                active_calls[call_id]["transferred_to"] = call_data.get("transfer_phone_number")
                active_calls[call_id]["transferred_at"] = datetime.utcnow().isoformat()
            logger.info(f"Call {call_id} transferred to {call_data.get('transfer_phone_number')}")
        
        return {"status": "ok", "event": event_type, "call_id": call_id}
        
    except HTTPException as e:
        logger.error(f"HTTPException in Retell webhook: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Error processing Retell webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Wisp Call Screening API",
        "version": "1.0.0",
        "endpoints": {
            "screening": "/wisp-screen",
            "webhook": "/retell-webhook",
            "health": "/health"
        }
    }


@app.post("/")
async def root_post(request: Request):
    """
    Root POST endpoint - handles Retell webhooks when configured to use root path.
    Retell webhooks can be configured to POST to / or /retell-webhook
    """
    # Delegate to the webhook handler
    x_retell_signature = request.headers.get("X-Retell-Signature")
    return await retell_webhook(request, x_retell_signature)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
