"""Ingestion Service Stub
Handles camera/video ingestion. Currently provides health endpoint.
"""
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Ingestion Service", version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", summary="Health Check")
async def health_check():
    """Liveness / readiness probe."""
    return {"status": "ok"}


@app.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_video(file: UploadFile = File(...)):
    """Handle video file uploads."""
    try:
        logger.info(f"Received file upload request. Filename: {file.filename}, Content-Type: {file.content_type}")
        
        # Check if file is provided
        if not file.filename:
            logger.error("No file provided in the request")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
            
        # Check file type
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            logger.error(f"Unsupported file type: {file_extension}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Create video directory if it doesn't exist
        VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving file to directory: {VIDEO_DIR}")
        
        # Save the uploaded file
        file_path = VIDEO_DIR / file.filename
        try:
            # Read file in chunks to handle large files
            with open(file_path, "wb") as buffer:
                while True:
                    chunk = await file.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    buffer.write(chunk)
            
            logger.info(f"Successfully saved file to {file_path}")
            
            # Start a background task to process the video
            thread = Thread(target=publish_frames, args=(file_path,))
            thread.daemon = True
            thread.start()
            
            return {
                "filename": file.filename, 
                "status": "uploaded", 
                "message": "Video is being processed",
                "video_id": str(hash(file.filename + str(time.time())))
            }
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            # Clean up partially uploaded file
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving file: {str(e)}"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


import os
import cv2
import numpy as np
from kafka import KafkaProducer
import json
import time
from threading import Thread
from pathlib import Path

# -----------------------------------------------------
# Configuration
# -----------------------------------------------------
KAFKA_BOOTSTRAP_SERVERS = [os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")]
FRAMES_TOPIC = os.getenv("FRAMES_TOPIC", "frames")
VIDEO_DIR = Path(os.getenv("VIDEO_DIR", "video samples"))
FRAME_STRIDE = int(os.getenv("FRAME_STRIDE", "30"))  # publish every N-th frame

producer: KafkaProducer | None = None


def publish_frames(video_path: Path):
    """Read video and publish frames to Kafka."""
    logger.info("Starting ingestion for %s", video_path.name)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error("Cannot open video %s", video_path)
        return
    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % FRAME_STRIDE == 0:
            _, buf = cv2.imencode(".jpg", frame)
            try:
                producer.send(
                    FRAMES_TOPIC,
                    key=json.dumps({"video_id": video_path.name, "frame_id": frame_idx}).encode("utf-8"),
                    value=buf.tobytes(),
                )
            except Exception as exc:
                logger.error("Failed to publish frame %s:%d => %s", video_path.name, frame_idx, exc)
        frame_idx += 1
    cap.release()
    logger.info("Finished ingestion for %s; published %d frames", video_path.name, frame_idx)


@app.on_event("startup")
async def startup_event():
    global producer
    logger.info("Ingestion service startup. Video dir: %s", VIDEO_DIR)
    if not VIDEO_DIR.exists():
        logger.error("Video directory %s not found", VIDEO_DIR)
        return
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            max_request_size=10485760,  # 10MB
            buffer_memory=33554432,  # 32MB
            compression_type='gzip'  # Enable compression
        )
    except Exception as exc:
        logger.error("Kafka producer init failed: %s", exc)
        return

    video_files = list(VIDEO_DIR.glob("*.mp4")) + list(VIDEO_DIR.glob("*.avi")) + list(VIDEO_DIR.glob("*.mkv"))
    if not video_files:
        logger.warning("No video files found in %s", VIDEO_DIR)
        return

    # Spawn a thread per video (simple). Could also process sequentially.
    for vp in video_files:
        Thread(target=publish_frames, args=(vp,), daemon=True).start()
    logger.info("Spawned %d ingestion threads", len(video_files))


@app.on_event("shutdown")
async def shutdown_event():
    if producer:
        producer.flush()
        producer.close()
        logger.info("Kafka producer closed")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
