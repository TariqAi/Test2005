#!/usr/bin/env python3
"""
AgentX AI RAG System Startup Script
This script starts both the FastAPI backend and Streamlit frontend
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    try:
        import fastapi
        import streamlit
        import chromadb
        import openai
        import elevenlabs
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists"""
    env_path = Path(".env")
    if env_path.exists():
        print("✅ Environment file found")
        return True
    else:
        print("❌ .env file not found")
        print("Please copy .env.example to .env and add your API keys")
        return False

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting FastAPI backend server...")
    try:
        # Start FastAPI server
        backend_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
        return backend_process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the Streamlit frontend"""
    print("🎨 Starting Streamlit frontend...")
    try:
        # Start Streamlit app
        frontend_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", 
            "run", "frontend/app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
        return frontend_process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def main():
    """Main startup function"""
    print("🤖 AgentX AI RAG System Startup")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment file
    if not check_env_file():
        sys.exit(1)
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        sys.exit(1)
    
    # Wait a bit for backend to start
    print("⏳ Waiting for backend to initialize...")
    time.sleep(5)
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 AgentX AI RAG System is now running!")
    print("=" * 50)
    print("📡 Backend API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🎨 Frontend: http://localhost:8501")
    print("=" * 50)
    print("\n💡 Tips:")
    print("- Make sure you have added your API keys to the .env file")
    print("- The system will automatically load HR data on first startup")
    print("- Use Ctrl+C to stop both services")
    print("\n🔧 Troubleshooting:")
    print("- If you see connection errors, wait a few seconds for services to start")
    print("- Check the console output for any error messages")
    print("- Ensure ports 8000 and 8501 are not in use by other applications")
    
    try:
        # Wait for user to stop the services
        print("\n⏸️  Press Ctrl+C to stop the system...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping AgentX AI RAG System...")
        
        # Terminate processes
        if backend_process:
            backend_process.terminate()
            print("✅ Backend stopped")
        
        if frontend_process:
            frontend_process.terminate()
            print("✅ Frontend stopped")
        
        print("👋 Thank you for using AgentX AI RAG System!")

if __name__ == "__main__":
    main()