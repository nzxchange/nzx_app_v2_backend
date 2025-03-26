#!/bin/bash
# start.sh for Render

cd /app
uvicorn main:app --host 0.0.0.0 --port $PORT 