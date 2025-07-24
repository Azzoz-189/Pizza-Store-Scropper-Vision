"""Tracking Service Stub
Tracks objects between frames. Provides health endpoint.
"""
import logging
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Tracking Service", version="0.1.0")


@app.get("/health", summary="Health Check")
async def health_check():
    return {"status": "ok"}

# TODO: Consume detections, apply DeepSORT/ByteTrack, publish results

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
