# Wisp
intent-based AI call filter

## Overview

Wisp is an AI-first call-screening service that uses Gemini 2.0 Flash-Lite to analyze incoming calls and automatically filter out scams while safely routing legitimate calls. The service integrates with Retell AI for call orchestration and Telnyx for SMS alerts.

## Architecture

- **Orchestration:** Retell AI (using ElevenLabs Voice)
- **AI Brain:** Gemini 2.0 Flash-Lite (Google SDK)
- **Telephony:** Telnyx (SIP Inbound configured as SRV, SMS Alerts)
- **Wisp Phone:** +14702282477 (Verizon with CCF)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `RETELL_API_KEY`: Your Retell AI API key
- `TELNYX_API_KEY`: Your Telnyx API key
- `MESSAGE_PROFILE_ID`: Your Telnyx messaging profile ID

### 3. Start the FastAPI Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 4. Expose with ngrok

To make the API accessible to Retell AI, expose it using ngrok:

```bash
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### 5. Configure Retell AI Custom Tool

1. Log into your Retell AI dashboard
2. Navigate to your agent configuration
3. Add a Custom Tool with the following settings:
   - **URL:** `https://your-ngrok-url.ngrok.io/wisp-screen`
   - **Method:** POST
   - **Headers:** 
     - `Content-Type: application/json`
   - **Request Body:** 
     ```json
     {
       "call_id": "{{call_id}}",
       "transcript": "{{transcript}}",
       "metadata": {}
     }
     ```

### 6. Verizon Configuration

#### iOS Live Voicemail Fix

**Important:** Turn off "Live Voicemail" in iOS Settings to prevent call routing issues:

1. Open Settings → Phone
2. Scroll to "Live Voicemail"
3. Toggle it OFF

#### Verizon Call Forwarding Activation

To activate call forwarding to your Telnyx number, dial:

```
*71 + [Your Telnyx Number]
```

For example, if your Telnyx number is `+1234567890`, dial:
```
*711234567890
```

This activates Conditional Call Forwarding (CCF) on your Verizon line.

## API Endpoints

### POST `/wisp-screen`

Main screening endpoint that analyzes call transcripts and executes appropriate actions.

**Request Body:**
```json
{
  "call_id": "string",
  "transcript": "string",
  "metadata": {}
}
```

**Response:**
```json
{
  "verdict": "SCAM" | "SAFE",
  "summary": "five word summary here",
  "call_id": "string"
}
```

### GET `/health`

Health check endpoint to verify service status and configuration.

### GET `/`

Root endpoint with API information.

## How It Works

### SCAM Detection Flow

1. Call transcript is sent to Gemini 2.0 Flash-Lite
2. Gemini analyzes and returns verdict + 5-word summary
3. If **SCAM:**
   - Retell terminates the call
   - Telnyx sends SMS to +14702282477: `🚨 Wisp Blocked: [Summary].`

### SAFE Call Flow

1. Call transcript is sent to Gemini 2.0 Flash-Lite
2. Gemini analyzes and returns verdict + 5-word summary
3. If **SAFE:**
   - Retell initiates warm transfer to +14702282477
   - Whisper message plays: `"Wisp here. Verified: [Summary]. Press any key to bridge."`
   - Telnyx sends SMS to +14702282477: `✅ Wisp Verified: [Summary]. Ringing you now.`

## Development

### Running in Development Mode

```bash
uvicorn main:app --reload
```

### Testing the API

```bash
curl -X POST http://localhost:8000/wisp-screen \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test-123",
    "transcript": "Hello, this is a test call",
    "metadata": {}
  }'
```

## Troubleshooting

- **ngrok URL not working:** Make sure ngrok is running and the URL is HTTPS (not HTTP)
- **Retell not connecting:** Verify the Custom Tool URL matches your ngrok URL exactly
- **SMS not sending:** Check Telnyx API key and message profile ID
- **Calls not forwarding:** Verify Verizon CCF is activated with `*71` code
- **Live Voicemail interfering:** Ensure Live Voicemail is disabled in iOS Settings

## License

MIT
