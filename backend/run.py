"""
Convenience script to start the ReSchedule FastAPI backend server.
Usage:
    python backend/run.py
"""
import os
import sys
import uvicorn

if __name__ == "__main__":
    # Ensure backend folder is in sys.path
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    print("=" * 60)
    print("Starting ReSchedule Backend on http://localhost:8000")
    print("Interactive Swagger API Documentation: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

