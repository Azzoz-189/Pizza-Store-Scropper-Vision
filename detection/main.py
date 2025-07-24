"""Detection Service Stub
Performs object detection on frames. Provides health endpoint.
"""
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Detection Service", version="0.1.0")


@app.get("/health", summary="Health Check")
async def health_check():
    return {"status": "ok"}

import os
import cv2
import numpy as np
from ultralytics import YOLO
from kafka import KafkaProducer, KafkaConsumer
import json
import asyncio
from threading import Thread
from pydantic import BaseModel

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
KAFKA_BOOTSTRAP_SERVERS = ["kafka:9092"]
FRAMES_TOPIC = os.getenv("FRAMES_TOPIC", "frames")
DETECTIONS_TOPIC = os.getenv("DETECTIONS_TOPIC", "detections")
MODEL_WEIGHTS = os.getenv("MODEL_WEIGHTS", "models/yolo12m-v2.pt")  # bundled custom weights

# Globals initialised in startup
model: torch.nn.Module | None = None
producer: KafkaProducer | None = None


class Box(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    conf: float
    cls: str


# ----------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------

def run_inference(img: np.ndarray):
    """Run model inference and return list of Box objects."""
    if model is None:
        raise RuntimeError("Model not loaded")
    results = model.predict(img, verbose=False)
    detections = []
    if not results:
        return detections
    r = results[0]
    for box in r.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        conf = box.conf[0].item()
        cls_idx = int(box.cls[0].item())
        label = model.names[cls_idx]
        detections.append(
            {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "conf": conf,
                "cls": label,
            }
        )
    return detections


# ----------------------------------------------------------------------
# REST API Endpoint
# ----------------------------------------------------------------------

@app.post("/detect", summary="Detect objects in uploaded image")
async def detect(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    detections = run_inference(img)

    # Publish detections to Kafka for downstream services
    if producer is not None:
        producer.send(DETECTIONS_TOPIC, value=detections)

    return {"detections": detections}


# ----------------------------------------------------------------------
# Kafka Frame Consumer (background thread)
# ----------------------------------------------------------------------

def consume_frames():
    global producer
    logger.info("Starting Kafka consumer on topic '%s'", FRAMES_TOPIC)
    try:
        consumer = KafkaConsumer(
            FRAMES_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: m,  # raw bytes
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id="detection-service",
        )
    except Exception as exc:
        logger.error("Kafka connection failed: %s", exc)
        return

    for msg in consumer:
        img_bytes = msg.value
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            continue
        detections = run_inference(img)
        if producer is not None:
            producer.send(DETECTIONS_TOPIC, value=detections)


# ----------------------------------------------------------------------
# Startup / Shutdown Events
# ----------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    global model, producer
    logger.info("Loading YOLO model: %s", MODEL_WEIGHTS)
    try:
        if os.path.isfile(MODEL_WEIGHTS):
            model = YOLO(MODEL_WEIGHTS)
        else:
            logger.warning("Weights file not found locally, using pretrained YOLOv8n")
            model = YOLO("yolov8n.pt")
        model.conf = 0.25  # confidence threshold
        logger.info("Model loaded with %d classes", len(model.names))
    except Exception as exc:
        logger.error("Failed to load model: %s", exc)
        raise

    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
    except Exception as exc:
        logger.error("Failed to init Kafka producer: %s", exc)
        producer = None

    # Start consumer thread
    thread = Thread(target=consume_frames, daemon=True)
    thread.start()
    logger.info("Kafka consumer thread started")


@app.on_event("shutdown")
async def shutdown_event():
    if producer:
        producer.close()
        logger.info("Kafka producer closed")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
