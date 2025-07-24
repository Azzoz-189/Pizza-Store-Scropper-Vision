"""Streaming Service
Provides:
1. REST metadata endpoint `/metadata` with current violation counts.
2. WebSocket endpoint `/ws` that streams detection/violation events (stub).

This is a minimal working stub; integrate actual Kafka frame streaming later.
"""
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")
import asyncio
import json
import time
from collections import defaultdict
from threading import Thread
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter
from kafka import KafkaConsumer

# Create API router
api_router = APIRouter()

# Define startup event
async def startup_event():
    logger.info("[STARTUP EVENT] FastAPI startup_event triggered!")
    print("[DEBUG] FastAPI startup_event triggered!")
    try:
        # Start Kafka consumer in a separate thread
        logger.info("Creating Kafka consumer thread...")
        thread = Thread(target=consume_violations, daemon=True, name="KafkaConsumerThread")
        thread.start()
        logger.info("Kafka consumer thread started")
        # Store the thread in the global app state (optional, for reference)
        app.state.kafka_consumer_thread = thread
    except Exception as e:
        logger.error(f"Error starting Kafka consumer: {e}", exc_info=True)
        raise

# Create FastAPI app and register startup event
app = FastAPI(title="Streaming Service", description="Streaming service for violation events")
logger.info("FastAPI app instantiated!")
print("[DEBUG] FastAPI app instantiated!")
app.add_event_handler("startup", startup_event)

logger = logging.getLogger("uvicorn")

KAFKA_BOOTSTRAP_SERVERS = ["kafka:9092"]
KAFKA_TOPIC = "frames"  # topic where frames are published by the ingestion service

app = FastAPI(title="Streaming Service", version="0.1.0")

# In-memory store of violation counts per video_id
violation_counts: Dict[str, int] = defaultdict(int)


class WebSocketManager:
    """Tracks connected WebSocket clients and handles broadcast."""

    def __init__(self):
        self.active: list[WebSocket] = []
        self.lock = asyncio.Lock()
        self.active_connections = 0  # Track number of active connections

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active.append(websocket)
            self.active_connections = len(self.active)
            logger.info(f"New WebSocket connection. Active connections: {self.active_connections}")

    async def disconnect(self, websocket: WebSocket):
        async with self.lock:
            if websocket in self.active:
                self.active.remove(websocket)
                self.active_connections = len(self.active)
                logger.info(f"WebSocket disconnected. Active connections: {self.active_connections}")
        logger.info("Client disconnected: %s", websocket.client)

    async def broadcast_json(self, data):
        async with self.lock:
            for ws in list(self.active):
                try:
                    await ws.send_json(data)
                except Exception as exc:
                    logger.warning("Failed to send to client: %s", exc)


manager = WebSocketManager()


@api_router.get("/health", summary="Health Check")
async def health_check():
    return {"status": "ok"}


@api_router.get("/metadata", summary="Violation metadata")
async def metadata():
    """Return aggregated violation counts per video (or 'default')."""
    return {"violations": violation_counts}


@api_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Streams violation events to frontend clients via WebSocket."""
    await manager.connect(websocket)
    try:
        while True:
            # This endpoint is server-push; we just wait for disconnect.
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# Kafka consumer background thread
# ---------------------------------------------------------------------------

def consume_violations():
    """Consume frame data and forward via WebSocket."""
    logger.info("[KAFKA] Starting Kafka consumer on topic '%s' with bootstrap servers: %s", 
                KAFKA_TOPIC, KAFKA_BOOTSTRAP_SERVERS)
    print("[DEBUG] [KAFKA] Starting Kafka consumer...")
    
    consumer = None
    while True:  # Reconnect loop
        try:
            # Initialize Kafka consumer
            logger.info("[KAFKA] Initializing Kafka consumer...")
            print("[DEBUG] [KAFKA] Creating Kafka consumer...")
            
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="latest",
                enable_auto_commit=True,
                group_id="streaming-service",
                max_poll_records=1,
                max_partition_fetch_bytes=10485760,
                fetch_max_bytes=10485760,
                request_timeout_ms=30000,
                session_timeout_ms=10000,
                heartbeat_interval_ms=3000
            )
            
            logger.info("[KAFKA] Consumer initialized. Subscribed to topic: %s", KAFKA_TOPIC)
            print(f"[DEBUG] [KAFKA] Consumer initialized. Subscribed to: {KAFKA_TOPIC}")
            
            # Main message consumption loop
            for message in consumer:
                try:
                    logger.info("[KAFKA] Received message from topic %s, partition %d, offset %d", 
                              message.topic, message.partition, message.offset)
                    print(f"[DEBUG] [KAFKA] Message received - Topic: {message.topic}, "
                          f"Partition: {message.partition}, Offset: {message.offset}")
                    
                    # Get the message data
                    data = message.value  # already deserialized JSON
                    
                    # Forward to WebSocket clients if any are connected
                    active_connections = len(manager.active) if hasattr(manager, 'active') else 0
                    logger.info("[WEBSOCKET] Active connections: %d", active_connections)
                    print(f"[DEBUG] [WEBSOCKET] Active connections: {active_connections}")
                    
                    if active_connections > 0:
                        logger.info("[WEBSOCKET] Sending update to %d clients", active_connections)
                        print(f"[DEBUG] [WEBSOCKET] Preparing to send update to {active_connections} clients")
                        
                        # Prepare the message to send
                        message_data = {
                            "type": "frame_update",
                            "message": "Frame data received",
                            "timestamp": data.get("timestamp", "unknown"),
                            "topic": message.topic,
                            "partition": message.partition,
                            "offset": message.offset
                        }
                        
                        try:
                            # Send the message to all connected WebSocket clients
                            logger.info("[WEBSOCKET] Broadcasting message: %s", message_data)
                            print(f"[DEBUG] [WEBSOCKET] Broadcasting message: {message_data}")
                            
                            # Get or create an event loop for this thread
                            try:
                                loop = asyncio.get_event_loop()
                            except RuntimeError as e:
                                if "There is no current event loop in thread" in str(e):
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                else:
                                    raise
                            
                            # Run the coroutine in the event loop
                            coro = manager.broadcast_json(message_data)
                            future = asyncio.run_coroutine_threadsafe(coro, loop)
                            
                            # Optional: Wait for the coroutine to complete
                            # This can be removed if you don't need to wait
                            try:
                                future.result(timeout=5)  # 5 second timeout
                                logger.info("[WEBSOCKET] Message broadcasted successfully")
                                print("[DEBUG] [WEBSOCKET] Message broadcasted successfully")
                            except Exception as e:
                                logger.error("[WEBSOCKET] Error waiting for broadcast to complete: %s", str(e))
                                print(f"[ERROR] [WEBSOCKET] Error waiting for broadcast to complete: {e}")
                                
                        except Exception as e:
                            logger.error("[WEBSOCKET] Error in broadcast setup: %s", str(e), exc_info=True)
                            print(f"[ERROR] [WEBSOCKET] Error in broadcast setup: {e}")
                    
                except json.JSONDecodeError as e:
                    logger.error("[KAFKA] Failed to decode message: %s", str(e))
                    print(f"[ERROR] [KAFKA] Failed to decode message: {e}")
                except Exception as e:
                    logger.error("[KAFKA] Error processing message: %s", str(e), exc_info=True)
                    print(f"[ERROR] [KAFKA] Error processing message: {e}")
                    
        except Exception as e:
            logger.error("[KAFKA] Consumer error: %s", str(e), exc_info=True)
            print(f"[ERROR] [KAFKA] Consumer error: {e}")
            
            # If we have a consumer, close it before reconnecting
            if consumer is not None:
                try:
                    consumer.close()
                    logger.info("[KAFKA] Closed consumer")
                    print("[DEBUG] [KAFKA] Closed consumer")
                except Exception as close_error:
                    logger.error("[KAFKA] Error closing consumer: %s", str(close_error))
                    print(f"[ERROR] [KAFKA] Error closing consumer: {close_error}")
            
            # Wait before reconnecting
            wait_time = 5
            logger.info("[KAFKA] Waiting %d seconds before reconnecting...", wait_time)
            print(f"[DEBUG] [KAFKA] Waiting {wait_time} seconds before reconnecting...")
            time.sleep(wait_time)
            
        finally:
            # Ensure consumer is closed on exit
            if consumer is not None:
                try:
                    consumer.close()
                except Exception as e:
                    logger.error("[KAFKA] Error closing consumer in finally: %s", str(e))
                    print(f"[ERROR] [KAFKA] Error closing consumer in finally: {e}")


# Debug endpoint to manually start Kafka consumer thread
@api_router.get("/test", summary="Manually start Kafka consumer thread for debugging")
async def test_start_kafka():
    logger.info("[TEST ENDPOINT] /test called. Starting Kafka consumer thread manually...")
    print("[DEBUG] /test endpoint called. Starting Kafka consumer thread manually...")
    thread = Thread(target=consume_violations, daemon=True, name="KafkaConsumerThreadTest")
    thread.start()
    app.state.kafka_consumer_thread_test = thread
    return {"status": "Kafka consumer thread started from /test endpoint"}

# Include the router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
