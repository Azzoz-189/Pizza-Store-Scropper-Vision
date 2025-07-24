"""Violation Service Stub
Evaluates scooper violations. Provides health endpoint.
"""
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kafka import KafkaProducer
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = ["kafka:9092"]
VIOLATION_TOPIC = "violations"

app = FastAPI(title="Violation Service", version="0.1.0")

# Create Kafka producer at startup
producer: KafkaProducer | None = None


class ViolationEvent(BaseModel):
    video_id: str
    frame_id: int | None = None
    description: str = "scooper_violation"



@app.get("/health", summary="Health Check")
async def health_check():
    return {"status": "ok"}

@app.post("/violation", summary="Publish a violation event")
async def publish_violation(event: ViolationEvent):
    if producer is None:
        raise HTTPException(status_code=500, detail="Kafka producer unavailable")
    payload = event.model_dump()
    try:
        producer.send(VIOLATION_TOPIC, value=payload)
        producer.flush()
    except Exception as exc:
        logger.error("Failed to send violation: %s", exc)
        raise HTTPException(status_code=500, detail="Kafka send failed")
    logger.info("Violation published: %s", payload)
    return {"status": "queued"}


@app.on_event("startup")
async def startup_event():
    global producer
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            linger_ms=10,
        )
        logger.info("Kafka producer initialised")
    except Exception as exc:
        logger.error("Failed to init Kafka producer: %s", exc)
        producer = None


@app.on_event("shutdown")
async def shutdown_event():
    if producer:
        producer.close()
        logger.info("Kafka producer closed")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
