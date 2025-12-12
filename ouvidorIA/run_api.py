#!/usr/bin/env python3
"""
Script to run the FastAPI backend locally.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
