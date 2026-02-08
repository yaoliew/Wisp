#!/bin/bash
# Run the FastAPI server from the project root
cd "$(dirname "$0")"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
