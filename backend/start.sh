#!/bin/sh
# Run database initialization
python init_db.py

# Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
