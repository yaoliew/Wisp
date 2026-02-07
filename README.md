# Wisp
intent-based AI call filter

## Overview

Wisp is an AI-first call-screening service that uses Gemini 2.5 Flash-Lite to analyze incoming calls and automatically filter out scams while safely routing legitimate calls. The service is fully Retell-native, using Retell AI for call orchestration, SMS alerts, and telephony infrastructure.

## Architecture

- **Orchestration:** Retell AI (using ElevenLabs Voice)
- **AI Brain:** Gemini 2.5 Flash-Lite (Google SDK via Retell Custom Tool)
- **Telephony:** Retell AI (phone numbers, call routing, SMS)
- **SMS:** Retell AI Chat API
- **Webhooks:** Retell call event webhooks for real-time monitoring

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
- `RETELL_AGENT_ID`: Your Retell AI agent ID (for SMS)
- `RETELL_WEBHOOK_SECRET`: Your Retell webhook secret (for webhook verification, optional but recommended)

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

### 6. Configure Retell Webhooks

1. In your Retell AI dashboard, navigate to Webhook settings
2. Add a webhook endpoint:
   - **URL:** `https://your-ngrok-url.ngrok.io/retell-webhook`
   - **Events:** Select `call_started`, `call_ended`, `call_transferred`
3. Copy the webhook secret and add it to your `.env` file as `RETELL_WEBHOOK_SECRET`

### 7. Set Up Retell Phone Numbers

1. In Retell AI dashboard, navigate to Phone Numbers
2. Purchase or configure a phone number for your Wisp service
3. Assign the number to your Retell agent
4. Update `WISP_PHONE` in `main.py` with your Retell phone number (or set via environment variable)

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

### POST `/retell-webhook`

Webhook endpoint for Retell call events. Handles `call_started`, `call_ended`, and `call_transferred` events.

**Headers:**
- `X-Retell-Signature`: Webhook signature for verification (if webhook secret is configured)

**Request Body:**
```json
{
  "event": "call_started" | "call_ended" | "call_transferred",
  "call": {
    "call_id": "string",
    "from_number": "string",
    "to_number": "string",
    ...
  },
  "data": {}
}
```

### GET `/`

Root endpoint with API information.

## How It Works

### Call Flow Overview

1. Incoming call arrives at Retell phone number
2. Retell webhook sends `call_started` event to `/retell-webhook`
3. Retell agent engages caller and collects transcript
4. Retell Custom Tool calls `/wisp-screen` with transcript
5. Gemini 2.5 Flash-Lite analyzes transcript and returns verdict + 5-word summary
6. System executes routing based on verdict

### SCAM Detection Flow

1. Call transcript is sent to Gemini 2.5 Flash-Lite via Custom Tool
2. Gemini analyzes and returns verdict + 5-word summary
3. If **SCAM:**
   - Retell terminates the call (with retry logic)
   - Retell SMS API sends alert: `🚨 Wisp Blocked: [Summary].`
   - Webhook receives `call_ended` event

### SAFE Call Flow

1. Call transcript is sent to Gemini 2.5 Flash-Lite via Custom Tool
2. Gemini analyzes and returns verdict + 5-word summary
3. If **SAFE:**
   - Retell initiates warm transfer to your phone number
   - Whisper message plays: `"Wisp here. Verified: [Summary]. Press any key to bridge."`
   - Retell SMS API sends alert: `✅ Wisp Verified: [Summary]. Ringing you now.`
   - Webhook receives `call_transferred` event

## Development

### Running in Development Mode

```bash
uvicorn main:app --reload
```

### Testing the API

#### Test Gemini Integration

Test the Gemini API integration independently:

```bash
python test_gemini.py
```

This will run two standard tests (scam and safe call scenarios) and optionally allow you to test with a custom transcript.

You can also pass a custom transcript as a command-line argument:

```bash
python test_gemini.py "Hello, this is a test call from a potential scammer asking for your credit card"
```

#### Test the Full API Endpoint

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
- **SMS not sending:** Check Retell API key and agent ID. Ensure SMS is enabled for your Retell agent
- **Webhook not receiving events:** Verify webhook URL in Retell dashboard and check ngrok is running
- **Webhook signature verification failing:** Ensure `RETELL_WEBHOOK_SECRET` matches the secret in Retell dashboard
- **Calls not routing:** Verify your Retell phone number is properly configured and assigned to your agent
- **Agent ID not found:** Get your agent ID from Retell dashboard under Agent settings

## License

MIT
