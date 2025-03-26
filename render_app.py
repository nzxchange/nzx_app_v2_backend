# render_app.py - Entry point for Render
import os
from main import app

# This file is specially designed for Render deployment
# It should not contain any code that creates a server
# Render will use the app from this file directly

# Print debug info
print(f"Starting render_app.py with PORT={os.environ.get('PORT')}") 