"""
Wisp - AI-first call-screening service backend
Fully Retell-native FastAPI backend for screening calls using Gemma3:1b via Ollama
Integrates with Retell AI for call orchestration and webhooks
"""
import os
import logging
import hmac
import hashlib
import asyncio
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import httpx
from datetime import datetime
from typing import Optional
from screening import analyze_with_gemini, Verdict
from database import init_database, create_or_update_call, get_all_calls, get_call, get_active_calls, get_stats, get_analytics_data, get_transcript_metrics

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Wisp Call Screening API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],  # Common frontend ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    await init_database()
    logger.info("Database initialized")

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
    summary: str = Field(..., description="Extremely brief summary of caller's intent")
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
                        "end_call": True,
                        "end_call_message": "This call has been blocked. Please remove this number from your call list. Goodbye."
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Successfully terminated call {call_id}")
                
                # Update call state (in-memory)
                terminated_at = datetime.utcnow().isoformat() + "Z"
                if call_id in active_calls:
                    active_calls[call_id]["status"] = "terminated"
                    active_calls[call_id]["terminated_at"] = terminated_at
                
                # Persist termination to database
                try:
                    call_record = {
                        "call_id": call_id,
                        "status": "terminated",
                        "terminated_at": terminated_at
                    }
                    # Merge with existing call data if available
                    if call_id in active_calls:
                        call_record.update(active_calls[call_id])
                    await create_or_update_call(call_record)
                except Exception as e:
                    logger.error(f"Failed to persist termination to database: {e}")
                
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


async def invoke_custom_transfer_call(call_id: str, target_number: str, whisper_message: str, retry_count: int = 3) -> bool:
    """
    Invoke custom transfer_call method via Retell API.
    
    This function attempts to trigger your custom transfer_call method in Retell.
    The exact API endpoint and payload format may vary depending on how your
    custom method is configured in Retell. You may need to adjust the payload
    structure based on your Retell configuration.
    """
    if not RETELL_API_KEY:
        logger.error("RETELL_API_KEY not configured, cannot invoke custom transfer")
        return False
    
    for attempt in range(retry_count):
        try:
            # Try different payload formats that might work with custom transfer methods
            # Adjust these based on your Retell custom tool configuration
            payload = {
                "transfer_phone_number": target_number,
                "whisper_message": whisper_message,
                "enable_voicemail_detection": False
            }
            
            # Alternative: If your custom method expects different parameters, uncomment and modify:
            # payload = {
            #     "action": "transfer",
            #     "phone_number": target_number,
            #     "message": whisper_message
            # }
            
            url = f"https://api.retellai.com/update-call/{call_id}"
            logger.info(f"Invoking custom transfer_call for call {call_id} to {target_number} (attempt {attempt + 1}/{retry_count})")
            logger.debug(f"Custom transfer payload: {payload}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {RETELL_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=10.0
                )
                
                logger.debug(f"Response status: {response.status_code}")
                try:
                    response_body = response.json()
                    logger.debug(f"Response body: {response_body}")
                except:
                    response_text = response.text
                    logger.debug(f"Response text: {response_text}")
                
                response.raise_for_status()
                logger.info(f"Successfully invoked custom transfer_call for call {call_id} to {target_number}")
                
                # Update call state
                transfer_initiated_at = datetime.utcnow().isoformat() + "Z"
                if call_id in active_calls:
                    active_calls[call_id]["transfer_initiated"] = True
                    active_calls[call_id]["transfer_target"] = target_number
                    active_calls[call_id]["transfer_initiated_at"] = transfer_initiated_at
                    active_calls[call_id]["transfer_method"] = "custom"
                
                # Persist to database
                try:
                    call_record = {
                        "call_id": call_id,
                        "transfer_initiated": True,
                        "transfer_target": target_number,
                        "transfer_initiated_at": transfer_initiated_at,
                        "transfer_method": "custom"
                    }
                    if call_id in active_calls:
                        call_record.update(active_calls[call_id])
                    await create_or_update_call(call_record)
                except Exception as e:
                    logger.error(f"Failed to persist custom transfer to database: {e}")
                
                return True
        except httpx.HTTPStatusError as e:
            error_details = {
                "status_code": e.response.status_code,
                "url": url,
                "call_id": call_id
            }
            try:
                error_body = e.response.json()
                error_details["error_body"] = error_body
                logger.error(f"HTTP error invoking custom transfer: {error_details}")
            except:
                error_text = e.response.text
                error_details["error_text"] = error_text
                logger.error(f"HTTP error invoking custom transfer: {error_details}")
            
            if e.response.status_code == 404:
                logger.warning(f"Call {call_id} not found (404) for custom transfer. Call may have ended or endpoint is incorrect.")
                return False
            elif attempt < retry_count - 1:
                logger.warning(f"Error invoking custom transfer (attempt {attempt + 1}/{retry_count}): {e.response.status_code}")
                await asyncio.sleep(1 * (attempt + 1))
            else:
                logger.error(f"Failed to invoke custom transfer after {retry_count} attempts")
                return False
        except Exception as e:
            logger.error(f"Unexpected error invoking custom transfer: {e}", exc_info=True)
            if attempt < retry_count - 1:
                await asyncio.sleep(1 * (attempt + 1))
            else:
                return False
    return False


async def warm_transfer_retell_call(call_id: str, target_number: str, whisper_message: str, retry_count: int = 3, use_custom: bool = False) -> bool:
    """Initiate warm transfer via Retell AI API with retry logic
    
    Args:
        call_id: The call ID to transfer
        target_number: Phone number to transfer to
        whisper_message: Message to whisper during transfer
        retry_count: Number of retry attempts
        use_custom: If True, use custom transfer_call method instead of standard API
    """
    # Use custom transfer method if requested
    if use_custom:
        return await invoke_custom_transfer_call(call_id, target_number, whisper_message, retry_count)
    
    if not RETELL_API_KEY:
        logger.error("RETELL_API_KEY not configured, cannot initiate warm transfer")
        return False
    
    # Verify call is still active before attempting transfer
    call_status = None
    if call_id in active_calls:
        call_status = active_calls[call_id].get("status")
        if call_status == "ended" or call_status == "terminated":
            logger.warning(f"Call {call_id} has status '{call_status}', cannot transfer")
            return False
    else:
        logger.warning(f"Call {call_id} not in active_calls, checking database...")
        # Check database to see if call exists and is active
        try:
            db_call = await get_call(call_id)
            if db_call:
                call_status = db_call.get("status")
                if call_status in ["ended", "terminated"]:
                    logger.warning(f"Call {call_id} has status '{call_status}' in database, cannot transfer")
                    return False
                logger.info(f"Call {call_id} found in database with status '{call_status}', proceeding with transfer")
            else:
                logger.warning(f"Call {call_id} not found in database or active_calls, but attempting transfer anyway (may be timing issue)")
        except Exception as e:
            logger.warning(f"Error checking database for call {call_id}: {e}, proceeding with transfer attempt")
    
    for attempt in range(retry_count):
        try:
            payload = {
                "transfer_phone_number": target_number,
                "enable_voicemail_detection": False,
                "whisper_message": whisper_message
            }
            
            url = f"https://api.retellai.com/update-call/{call_id}"
            logger.info(f"Attempting warm transfer for call {call_id} to {target_number} (attempt {attempt + 1}/{retry_count})")
            logger.debug(f"Transfer payload: {payload}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {RETELL_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=10.0
                )
                
                # Log response details for debugging
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                
                try:
                    response_body = response.json()
                    logger.debug(f"Response body: {response_body}")
                except:
                    response_text = response.text
                    logger.debug(f"Response text: {response_text}")
                
                response.raise_for_status()
                logger.info(f"Successfully initiated warm transfer for call {call_id} to {target_number}")
                
                # Update call state (in-memory)
                transfer_initiated_at = datetime.utcnow().isoformat() + "Z"
                if call_id in active_calls:
                    active_calls[call_id]["transfer_initiated"] = True
                    active_calls[call_id]["transfer_target"] = target_number
                    active_calls[call_id]["transfer_initiated_at"] = transfer_initiated_at
                
                # Persist transfer initiation to database
                try:
                    call_record = {
                        "call_id": call_id,
                        "transfer_initiated": True,
                        "transfer_target": target_number,
                        "transfer_initiated_at": transfer_initiated_at
                    }
                    # Merge with existing call data if available
                    if call_id in active_calls:
                        call_record.update(active_calls[call_id])
                    await create_or_update_call(call_record)
                except Exception as e:
                    logger.error(f"Failed to persist transfer initiation to database: {e}")
                
                return True
        except httpx.HTTPStatusError as e:
            # Log detailed error information
            error_details = {
                "status_code": e.response.status_code,
                "url": url,
                "call_id": call_id
            }
            try:
                error_body = e.response.json()
                error_details["error_body"] = error_body
                logger.error(f"HTTP error details: {error_details}")
            except:
                error_text = e.response.text
                error_details["error_text"] = error_text
                logger.error(f"HTTP error details: {error_details}")
            
            if e.response.status_code == 404:
                logger.warning(f"Call {call_id} not found (404), cannot transfer. Call may have already ended or call_id is invalid.")
                # Check if call exists in database
                try:
                    db_call = await get_call(call_id)
                    if db_call:
                        logger.info(f"Call {call_id} exists in database with status: {db_call.get('status')}")
                    else:
                        logger.warning(f"Call {call_id} not found in database either")
                except Exception as db_error:
                    logger.error(f"Error checking database for call {call_id}: {db_error}")
                return False
            elif e.response.status_code == 401:
                logger.error(f"Authentication failed (401). Check RETELL_API_KEY configuration.")
                return False
            elif e.response.status_code == 400:
                logger.error(f"Bad request (400). Check payload format and call_id format.")
                return False
            else:
                if attempt < retry_count - 1:
                    logger.warning(f"Error initiating transfer for call {call_id} (attempt {attempt + 1}/{retry_count}): {e.response.status_code}")
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"Error initiating warm transfer after {retry_count} attempts: {e.response.status_code}")
                    return False
        except httpx.RequestError as e:
            logger.error(f"Request error (network/timeout) for call {call_id}: {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(1 * (attempt + 1))
            else:
                return False
        except Exception as e:
            logger.error(f"Unexpected error initiating transfer for call {call_id}: {e}", exc_info=True)
            if attempt < retry_count - 1:
                await asyncio.sleep(1 * (attempt + 1))
            else:
                return False
    return False


@app.post("/wisp-screen", response_model=ScreeningResponse)
async def wisp_screen(request: Request):
    """
    Main screening endpoint for Wisp call screening service.
    
    Analyzes call transcript with Gemma3:1b via Ollama and executes
    appropriate actions based on verdict (SCAM or SAFE).
    Works with both Custom Tool calls and webhook-driven flows.
    
    Accepts two request formats:
    1. Direct format: {"call_id": "...", "transcript": "...", "metadata": {...}}
    2. Retell Custom Tool format: {"args": {"call_id": "...", "transcript": "..."}, ...}
    """
    
    # Parse request body
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse request body: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    
    # Extract call_id and transcript from either format
    # Retell Custom Tool format: {"args": {"call_id": "...", "transcript": "..."}}
    # Direct format: {"call_id": "...", "transcript": "..."}
    if isinstance(body, dict) and "args" in body and isinstance(body["args"], dict):
        # Retell Custom Tool format
        call_id = body["args"].get("call_id")
        transcript = body["args"].get("transcript")
        metadata = body.get("metadata") or body["args"].get("metadata")
    else:
        # Direct format
        call_id = body.get("call_id") if isinstance(body, dict) else None
        transcript = body.get("transcript") if isinstance(body, dict) else None
        metadata = body.get("metadata") if isinstance(body, dict) else None
    
    # Validate required fields
    if not call_id:
        raise HTTPException(status_code=422, detail="Field 'call_id' is required")
    if not transcript:
        raise HTTPException(status_code=422, detail="Field 'transcript' is required")
    
    logger.info(f"Received screening request for call {call_id}")
    
    # Check if call is in active calls (from webhook)
    call_state = active_calls.get(call_id, {})
    
    # Step 1: Analyze transcript with Gemma
    verdict, summary = await analyze_with_gemini(transcript)
    
    logger.info(f"Screening result for call {call_id}: verdict={verdict.value}, summary={summary}")
    
    # Update call state with screening result (in-memory)
    screened_at = datetime.utcnow().isoformat() + "Z"
    if call_id in active_calls:
        active_calls[call_id]["screening_verdict"] = verdict.value
        active_calls[call_id]["screening_summary"] = summary
        active_calls[call_id]["screened_at"] = screened_at
        active_calls[call_id]["transcript"] = transcript
    
    # Persist screening results and transcript to database
    try:
        # First, get existing call data from database to preserve all fields
        existing_call = await get_call(call_id)
        
        call_record = {
            "call_id": call_id,
        }
        
        # Merge with existing database data first (to preserve other fields)
        if existing_call:
            call_record.update(existing_call)
            logger.debug(f"Existing call data for {call_id}: verdict={existing_call.get('screening_verdict')}")
        
        # Then merge with active_calls data (which may have more recent updates)
        if call_id in active_calls:
            call_record.update(active_calls[call_id])
            logger.debug(f"After merging active_calls for {call_id}: verdict={call_record.get('screening_verdict')}")
        
        # CRITICAL: Set screening fields LAST to ensure they're never overwritten
        call_record["screening_verdict"] = verdict.value
        call_record["screening_summary"] = summary
        call_record["screened_at"] = screened_at
        call_record["transcript"] = transcript
        
        logger.info(f"Persisting call {call_id} with verdict={call_record['screening_verdict']}")
        await create_or_update_call(call_record)
        logger.info(f"Successfully persisted call {call_id} with verdict={call_record['screening_verdict']}")
    except Exception as e:
        logger.error(f"Failed to persist screening results to database: {e}", exc_info=True)
    
    # Step 2: Execute based on verdict
    if verdict == Verdict.SCAM:
        # SCAM flow: Terminate call
        logger.info(f"SCAM detected for call {call_id}. Terminating call.")
        
        # Terminate call via Retell (with retry logic)
        termination_success = await terminate_retell_call(call_id)
        if not termination_success:
            logger.error(f"Failed to terminate call {call_id}")
        
    else:  # SAFE
        # SAFE flow: Warm transfer + Whisper
        logger.info(f"SAFE call detected for call {call_id}. Initiating warm transfer.")
        
        # Create whisper message
        whisper_message = f"Wisp here. Verified: {summary}. Press any key to bridge."
        
        # Initiate warm transfer via Retell (with retry logic)
        # Set use_custom=True to use custom transfer_call method
        use_custom_transfer = os.getenv("USE_CUSTOM_TRANSFER", "false").lower() == "true"
        transfer_success = await warm_transfer_retell_call(call_id, WISP_PHONE, whisper_message, use_custom=use_custom_transfer)
        if not transfer_success:
            logger.error(f"Failed to initiate warm transfer for call {call_id}")
    
    return ScreeningResponse(
        verdict=verdict,
        summary=summary,
        call_id=call_id
    )


@app.get("/api/calls")
async def get_calls_endpoint(
    limit: Optional[int] = Query(None, description="Limit number of calls returned"),
    status: Optional[str] = Query(None, description="Filter by status"),
    verdict: Optional[str] = Query(None, description="Filter by screening_verdict")
):
    """
    Fetch all calls with optional filters.
    
    Query parameters:
    - limit: Maximum number of calls to return
    - status: Filter by call status (e.g., 'active', 'ended')
    - verdict: Filter by screening verdict ('SCAM', 'SAFE')
    """
    try:
        calls = await get_all_calls(limit=limit, status=status, verdict=verdict)
        return {"calls": calls, "count": len(calls)}
    except Exception as e:
        logger.error(f"Error fetching calls: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching calls: {str(e)}")


@app.get("/api/calls/active")
async def get_active_calls_endpoint():
    """
    Fetch currently active calls.
    Active calls are those with status='active' or status IS NULL AND ended_at IS NULL.
    """
    try:
        calls = await get_active_calls()
        return {"calls": calls, "count": len(calls)}
    except Exception as e:
        logger.error(f"Error fetching active calls: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching active calls: {str(e)}")


@app.get("/api/calls/{call_id}")
async def get_call_endpoint(call_id: str):
    """
    Fetch a single call by call_id.
    """
    try:
        call = await get_call(call_id)
        if call is None:
            raise HTTPException(status_code=404, detail=f"Call {call_id} not found")
        return call
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching call {call_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching call: {str(e)}")


@app.get("/api/stats")
async def get_stats_endpoint():
    """
    Fetch dashboard statistics.
    Returns:
    - blocked_this_week: Count of SCAM verdicts in last 7 days
    - total_protected: Total count of SCAM verdicts
    - blocked_last_week: Count of SCAM verdicts in previous week
    - trend_percentage: Percentage change from last week
    """
    try:
        stats = await get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@app.get("/api/analytics")
async def get_analytics_endpoint(
    period: Optional[str] = Query("daily", description="Period: daily, weekly, or monthly")
):
    """
    Fetch analytics data for the analytics page.
    
    Query parameters:
    - period: "daily" (default), "weekly", or "monthly"
    
    Returns:
    - calls_by_period: Array of {date, count} for total calls
    - blocked_by_period: Array of {date, count} for blocked calls (verdict='SCAM')
    - scam_safe_ratio: {scam: count, safe: count}
    - avg_call_duration: Average duration in seconds
    - top_scam_categories: Array of {category, count} with fake categories
    """
    try:
        if period not in ["daily", "weekly", "monthly"]:
            raise HTTPException(status_code=400, detail="Period must be 'daily', 'weekly', or 'monthly'")
        
        analytics = await get_analytics_data(period)
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")


@app.get("/api/transcripts/metrics")
async def get_transcript_metrics_endpoint():
    """
    Fetch transcript metrics for the transcripts page.
    
    Returns:
    - average_word_count: Average number of words per transcript
    - total_transcripts: Total number of calls with transcripts
    """
    try:
        metrics = await get_transcript_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error fetching transcript metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching transcript metrics: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from screening import OLLAMA_MODEL
    import ollama
    ollama_available = False
    try:
        ollama.list()
        ollama_available = True
    except:
        pass
    return {
        "status": "healthy",
        "service": "Wisp Call Screening API",
        "ollama_configured": ollama_available,
        "ollama_model": OLLAMA_MODEL,
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
            # Store call state in memory
            call_record = {
                "call_id": call_id,
                "from_number": call_data.get("from_number"),
                "to_number": call_data.get("to_number"),
                "started_at": datetime.utcnow().isoformat() + "Z",
                "status": "active"
            }
            active_calls[call_id] = call_record
            
            # Persist to database
            try:
                await create_or_update_call(call_record)
            except Exception as e:
                logger.error(f"Failed to persist call_started to database: {e}")
            
            logger.info(f"Call {call_id} started, stored in active calls and database")
            
        elif event_type == "call_ended":
            # Update call state (in-memory)
            ended_at = datetime.utcnow().isoformat() + "Z"
            if call_id in active_calls:
                active_calls[call_id]["status"] = "ended"
                active_calls[call_id]["ended_at"] = ended_at
            
            # Persist call end to database
            try:
                # First, get existing call data from database to preserve all fields (especially screening_verdict)
                existing_call = await get_call(call_id)
                
                call_record = {
                    "call_id": call_id,
                    "status": "ended",
                    "ended_at": ended_at
                }
                
                # Merge with existing database data first (to preserve screening_verdict, etc.)
                if existing_call:
                    call_record.update(existing_call)
                    logger.debug(f"Call {call_id} ended - existing verdict: {existing_call.get('screening_verdict')}")
                
                # Then merge with active_calls data (which may have more recent updates)
                if call_id in active_calls:
                    call_record.update(active_calls[call_id])
                
                # Ensure status and ended_at are set correctly (active_calls might have overwritten)
                call_record["status"] = "ended"
                call_record["ended_at"] = ended_at
                
                logger.info(f"Persisting call_ended for {call_id} with verdict: {call_record.get('screening_verdict')}")
                await create_or_update_call(call_record)
            except Exception as e:
                logger.error(f"Failed to persist call_ended to database: {e}")
            
            logger.info(f"Call {call_id} ended")
            
        elif event_type == "call_transferred":
            # Update call state with transfer information (in-memory)
            transferred_at = datetime.utcnow().isoformat() + "Z"
            transferred_to = call_data.get("transfer_phone_number")
            if call_id in active_calls:
                active_calls[call_id]["transferred_to"] = transferred_to
                active_calls[call_id]["transferred_at"] = transferred_at
            
            # Persist transfer to database
            try:
                call_record = {
                    "call_id": call_id,
                    "transferred_to": transferred_to,
                    "transferred_at": transferred_at
                }
                # Merge with existing call data if available
                if call_id in active_calls:
                    call_record.update(active_calls[call_id])
                await create_or_update_call(call_record)
            except Exception as e:
                logger.error(f"Failed to persist call_transferred to database: {e}")
            
            logger.info(f"Call {call_id} transferred to {transferred_to}")
        
        return {"status": "ok", "event": event_type, "call_id": call_id}
        
    except HTTPException as e:
        logger.error(f"HTTPException in Retell webhook: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Error processing Retell webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transfer-call")
async def transfer_call_endpoint(request: Request):
    """
    Transfer a call using either standard Retell API or custom transfer_call method.
    This endpoint can be called directly or by Retell's custom tool.
    
    Accepts both query parameters and JSON body (for Retell custom tool calls).
    """
    if not RETELL_API_KEY:
        raise HTTPException(status_code=500, detail="RETELL_API_KEY not configured")
    
    # Parse request - support both query params and JSON body (for Retell custom tools)
    try:
        body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    except:
        body = {}
    
    # Extract parameters from query string or body
    call_id = body.get("call_id") or body.get("args", {}).get("call_id") or request.query_params.get("call_id")
    target_number = body.get("target_number") or body.get("args", {}).get("target_number") or request.query_params.get("target_number")
    whisper_message = body.get("whisper_message") or body.get("args", {}).get("whisper_message") or request.query_params.get("whisper_message")
    use_custom = body.get("use_custom", False) if isinstance(body.get("use_custom"), bool) else request.query_params.get("use_custom", "false").lower() == "true"
    
    if not call_id:
        raise HTTPException(status_code=422, detail="call_id is required")
    
    target = target_number or WISP_PHONE
    whisper = whisper_message or f"Wisp here. Press any key to bridge."
    
    logger.info(f"Transfer call requested for call {call_id} to {target} (custom={use_custom})")
    
    # Check if call exists in active calls or database
    call_info = {
        "in_active_calls": call_id in active_calls,
        "active_call_status": active_calls.get(call_id, {}).get("status") if call_id in active_calls else None
    }
    
    try:
        db_call = await get_call(call_id)
        call_info["in_database"] = db_call is not None
        if db_call:
            call_info["db_status"] = db_call.get("status")
    except Exception as e:
        logger.warning(f"Error checking database for call {call_id}: {e}")
        call_info["db_check_error"] = str(e)
    
    # Attempt the transfer
    if use_custom:
        success = await invoke_custom_transfer_call(call_id, target, whisper)
    else:
        success = await warm_transfer_retell_call(call_id, target, whisper, use_custom=False)
    
    return {
        "success": success,
        "call_id": call_id,
        "target_number": target,
        "whisper_message": whisper,
        "method": "custom" if use_custom else "standard",
        "call_info": call_info,
        "message": "Transfer initiated successfully" if success else "Transfer failed - check logs for details"
    }


@app.post("/api/test-transfer")
async def test_transfer_endpoint(
    call_id: str = Query(..., description="Call ID to test transfer with"),
    target_number: Optional[str] = Query(None, description="Target phone number (defaults to WISP_PHONE)"),
    use_custom: bool = Query(False, description="Use custom transfer_call method")
):
    """
    Test endpoint to verify warm transfer functionality.
    This endpoint allows manual testing of the warm transfer API call.
    """
    if not RETELL_API_KEY:
        raise HTTPException(status_code=500, detail="RETELL_API_KEY not configured")
    
    target = target_number or WISP_PHONE
    whisper_message = "Test transfer from Wisp. Press any key to bridge."
    
    logger.info(f"Test transfer requested for call {call_id} to {target} (custom={use_custom})")
    
    # Check if call exists in active calls or database
    call_info = {
        "in_active_calls": call_id in active_calls,
        "active_call_status": active_calls.get(call_id, {}).get("status") if call_id in active_calls else None
    }
    
    try:
        db_call = await get_call(call_id)
        call_info["in_database"] = db_call is not None
        if db_call:
            call_info["db_status"] = db_call.get("status")
    except Exception as e:
        logger.warning(f"Error checking database for call {call_id}: {e}")
        call_info["db_check_error"] = str(e)
    
    # Attempt the transfer
    if use_custom:
        success = await invoke_custom_transfer_call(call_id, target, whisper_message)
    else:
        success = await warm_transfer_retell_call(call_id, target, whisper_message, use_custom=False)
    
    return {
        "success": success,
        "call_id": call_id,
        "target_number": target,
        "method": "custom" if use_custom else "standard",
        "call_info": call_info,
        "message": "Transfer initiated successfully" if success else "Transfer failed - check logs for details"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Wisp Call Screening API",
        "version": "1.0.0",
        "endpoints": {
            "screening": "/wisp-screen",
            "webhook": "/retell-webhook",
            "health": "/health",
            "transfer_call": "/api/transfer-call",
            "test_transfer": "/api/test-transfer"
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
