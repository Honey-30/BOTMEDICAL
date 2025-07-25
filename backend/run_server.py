#!/usr/bin/env python3
"""
Agentic AI Project Management Assistant - Backend Entry Point
Run with: python run_server.py
"""

import uvicorn
import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    print("🚀 Starting Agentic AI Project Management Assistant Backend...")
    print(f"📡 Server will run on http://{host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True
    )