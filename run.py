"""
Application Entry Point.
Runs the FastAPI server using Uvicorn.
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    reload = os.getenv("RELOAD", "True").lower() in ("true", "1", "yes")

    print(f"Starting Library Management System on http://{host}:{port}")
    print(f"Interactive API Documentation: http://{host}:{port}/docs")
    uvicorn.run("presentation.main:app", host=host, port=port, reload=reload)
