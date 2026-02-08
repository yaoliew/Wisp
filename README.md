# Wisp
intent-based AI call filter

## Purpose

Wisp is an AI-first call-screening service designed to automatically filter out scam calls while safely routing legitimate calls to you. The system analyzes incoming call transcripts in real-time using local AI, determines whether a call is a scam or safe, and automatically terminates scam calls or transfers legitimate ones to your phone with a brief verification message. This eliminates the need to manually screen every call and protects you from phone scams and fraud.

## Tools Utilized

### Backend
- **FastAPI** - Modern Python web framework for building REST APIs
- **Uvicorn** - ASGI server for running FastAPI applications
- **Python 3.10+** - Programming language
- **SQLite** (via aiosqlite) - Lightweight database for storing call records
- **Ollama** - Local LLM runtime for running AI models
- **Gemma3:1b** - Google's lightweight language model for transcript analysis
- **httpx** - Async HTTP client for API calls
- **Pydantic** - Data validation using Python type annotations
- **python-dotenv** - Environment variable management

### Frontend
- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Radix UI** - Unstyled, accessible component primitives
  - @radix-ui/react-dialog
  - @radix-ui/react-label
  - @radix-ui/react-select
  - @radix-ui/react-switch
  - @radix-ui/react-slot
- **React Router** - Client-side routing
- **Recharts** - Charting library for analytics
- **Lucide React** - Icon library
- **date-fns** - Date utility library
- **class-variance-authority** - Component variant management
- **clsx** & **tailwind-merge** - Conditional class utilities

### External Services
- **Retell AI** - Telephony infrastructure and call orchestration
- **ngrok** - Local development tunneling (for exposing backend to Retell)

## Problems Encountered & Solutions

### Problem 1: Retell Custom Tool Not Triggering on Subsequent Calls
**Issue:** After the first successful call screening, subsequent calls were bypassing the screening endpoint and going straight to the phone without analysis.

**Solution:** The issue was in the Retell AI configuration. We discovered that the Custom Tool URL needed to be verified and the Retell agent needed to be explicitly configured to call the tool on every call, not just conditionally. We also added comprehensive logging to track when the `/wisp-screen` endpoint was called vs. when it wasn't, which helped diagnose the configuration issue.

### Problem 2: Webhook Signature Verification
**Issue:** During development, webhook signature verification was failing, causing legitimate webhooks to be rejected.

**Solution:** We implemented a development mode that logs signature verification failures but allows requests through. In production, strict verification can be enabled. We also improved the signature parsing logic to handle Retell's specific signature format (`v=<timestamp>,d=<signature>`).

### Problem 3: Call Transfer Timing Issues
**Issue:** Sometimes calls would be transferred before the screening verdict was determined, or transfers would fail because the call had already ended.

**Solution:** We added call status checks before attempting transfers, verifying that calls are still active both in-memory state and the database. We also implemented retry logic with exponential backoff for all Retell API calls to handle transient failures.

### Problem 4: React Router and GitHub Pages Deployment
**Issue:** When deploying to GitHub Pages, React Router's `BrowserRouter` caused 404 errors on page refresh due to GitHub Pages serving from a subpath.

**Solution:** We configured Vite with a base path and switched to `HashRouter` for GitHub Pages deployment, which uses URL hashes instead of paths, avoiding the 404 issue entirely.

### Problem 5: CORS Configuration
**Issue:** Frontend running on localhost couldn't access the backend API due to CORS restrictions.

**Solution:** We configured FastAPI's CORS middleware to allow requests from common frontend development ports (localhost:3000, localhost:5173, localhost:5174) and added support for GitHub Pages domains in production.

## Credits & Acknowledgments

### APIs & Services
- **[Retell AI](https://retellai.com/)** - Telephony infrastructure, call orchestration, and phone number management
- **[Ollama](https://ollama.ai/)** - Local LLM runtime for running AI models
- **[Google Gemma](https://ai.google.dev/gemma)** - Open-source language model (Gemma3:1b) used for call transcript analysis

### Frameworks & Libraries
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[React](https://react.dev/)** - UI library
- **[Vite](https://vitejs.dev/)** - Build tool
- **[Tailwind CSS](https://tailwindcss.com/)** - CSS framework
- **[Radix UI](https://www.radix-ui.com/)** - Accessible component primitives
- **[Recharts](https://recharts.org/)** - Charting library
- **[React Router](https://reactrouter.com/)** - Routing library
- **[Lucide](https://lucide.dev/)** - Icon library
- **[date-fns](https://date-fns.org/)** - Date utilities

### Development Tools
- **[ngrok](https://ngrok.com/)** - Local development tunneling
- **[TypeScript](https://www.typescriptlang.org/)** - Type-safe JavaScript
- **[ESLint](https://eslint.org/)** - Code linting

## Architecture

- **Orchestration:** Retell AI (call handling and telephony infrastructure)
- **AI Brain:** Ollama with Gemma3:1b (local LLM for transcript analysis)
- **Backend:** FastAPI (Python) with SQLite database
- **Frontend:** React + TypeScript with Vite
- **Telephony:** Retell AI (phone numbers, call routing, webhooks)

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
- `RETELL_API_KEY`: Your Retell AI API key
- `RETELL_WEBHOOK_SECRET`: Your Retell webhook secret (for webhook verification, optional but recommended)
- `OLLAMA_MODEL`: Ollama model to use (default: "gemma3:1b")
- `OLLAMA_HOST`: Ollama server URL (default: "http://localhost:11434")

### 3. Start the FastAPI Server

**Option 1: Run from backend directory (Recommended)**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or use the convenience script:
```bash
./backend/run.sh
```

**Option 2: Run from project root**
```bash
# Set PYTHONPATH to include project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the convenience script:
```bash
./run_backend.sh
```

**Important:** When running from the `backend/` directory, use `main:app`. When running from the project root, use `backend.main:app` and ensure PYTHONPATH includes the project root.

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
4. Update `WISP_PHONE` in `backend/main.py` with your Retell phone number (or set via environment variable)

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
3. Backend stores call metadata in SQLite database
4. Retell agent engages caller and collects transcript
5. Retell Custom Tool calls `/wisp-screen` endpoint with transcript
6. Backend sends transcript to Ollama (Gemma3:1b) for analysis
7. Ollama returns verdict (SCAM/SAFE) + 5-word summary
8. Backend stores screening results in database
9. System executes routing based on verdict

### SCAM Detection Flow

1. Call transcript is sent to Ollama via `/wisp-screen` endpoint
2. Gemma3:1b model analyzes transcript and returns SCAM verdict + summary
3. Backend stores verdict in database
4. Backend calls Retell API to terminate the call (with retry logic)
5. Retell webhook sends `call_ended` event
6. Backend updates database with final call state

### SAFE Call Flow

1. Call transcript is sent to Ollama via `/wisp-screen` endpoint
2. Gemma3:1b model analyzes transcript and returns SAFE verdict + summary
3. Backend stores verdict in database
4. Backend calls Retell API to initiate warm transfer to your phone number
5. Whisper message plays: `"Wisp here. Verified: [Summary]. Press any key to bridge."`
6. Retell webhook sends `call_transferred` event
7. Backend updates database with transfer information

## Development

### Running in Development Mode

```bash
cd backend
uvicorn main:app --reload
```

Or from the project root:

```bash
uvicorn backend.main:app --reload
```

### Testing the API

#### Test Ollama Integration

Test the Ollama/Gemma integration independently:

```bash
cd backend
python screening.py
```

This will run a test with a sample transcript and show the verdict and summary. You can also pass a custom transcript as a command-line argument:

```bash
cd backend
python screening.py "Hello, this is a test call from a potential scammer asking for your credit card"
```

**Note:** Make sure Ollama is running locally with the Gemma3:1b model installed:
```bash
ollama pull gemma3:1b
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
- **Webhook not receiving events:** Verify webhook URL in Retell dashboard and check ngrok is running
- **Webhook signature verification failing:** Ensure `RETELL_WEBHOOK_SECRET` matches the secret in Retell dashboard
- **Calls not routing:** Verify your Retell phone number is properly configured and assigned to your agent

## License

MIT
