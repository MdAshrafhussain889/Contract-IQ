#!/bin/bash
# Start ContractIQ FastAPI application with environment variables loaded

cd "$(dirname "$0")"

# Load environment variables from .env
export $(cat .env | grep -v '#' | grep -v '^$' | xargs)

# Activate virtual environment
source venv/bin/activate

# Start the application
python main.py
