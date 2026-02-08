#!/bin/bash
# Run the FastAPI server from the backend directory
cd "$(dirname "$0")"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
