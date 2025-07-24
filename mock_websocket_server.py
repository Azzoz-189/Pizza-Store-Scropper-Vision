import asyncio
import websockets
import json
import random
import time
import os
from datetime import datetime
from pathlib import Path

# Configuration
VIDEO_SAMPLES_DIR = os.path.join('ingestion', 'video samples')
WS_PORT = 8004

# Mock violation types for simulation
VIOLATION_TYPES = [
    "No Hairnet",
    "Bare Hand Contact",
    "No Gloves",
    "Improper Food Storage",
    "Cross Contamination",
    "Expired Food"
]

# Mock frame data
def generate_mock_frame(video_id):
    """Generate mock frame data with random violations."""
    frame_data = {
        "type": "frame",
        "video_id": video_id,
        "timestamp": datetime.utcnow().isoformat(),
        "frame_number": random.randint(1, 1000),
        "detections": []
    }
    
    # Randomly add 0-2 violations per frame
    if random.random() > 0.7:  # 30% chance of having a violation
        num_violations = random.randint(1, 2)
        for _ in range(num_violations):
            violation = {
                "type": "violation",
                "violation_type": random.choice(VIOLATION_TYPES),
                "confidence": round(random.uniform(0.7, 0.98), 2),
                "bbox": {
                    "x1": random.randint(0, 700),
                    "y1": random.randint(0, 500),
                    "x2": random.randint(100, 800),
                    "y2": random.randint(100, 600)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            frame_data["detections"].append(violation)
    
    return frame_data

async def mock_analysis(websocket, path):
    """Handle WebSocket connection and send mock analysis data."""
    print("Client connected")
    
    try:
        # Wait for the client to send the video ID
        message = await websocket.recv()
        data = json.loads(message)
        video_id = data.get("video_id")
        
        if not video_id:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "No video_id provided"
            }))
            return
        
        print(f"Starting mock analysis for video: {video_id}")
        
        # Send initial status
        await websocket.send(json.dumps({
            "type": "status",
            "message": "Starting analysis..."
        }))
        
        # Simulate analysis by sending frames
        for _ in range(50):  # Send 50 frames
            frame_data = generate_mock_frame(video_id)
            await websocket.send(json.dumps(frame_data))
            await asyncio.sleep(0.5)  # Simulate processing time
        
        # Send completion message
        await websocket.send(json.dumps({
            "type": "status",
            "message": "Analysis complete"
        }))
        
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Connection closed")

if __name__ == "__main__":
    # Create video samples directory if it doesn't exist
    os.makedirs(VIDEO_SAMPLES_DIR, exist_ok=True)
    
    print("=" * 50)
    print("Mock Video Analysis Server")
    print("=" * 50)
    print(f"WebSocket URL: ws://localhost:{WS_PORT}/ws")
    print(f"Video samples directory: {os.path.abspath(VIDEO_SAMPLES_DIR)}")
    print("\nAvailable sample videos:")
    
    # List available video files
    video_files = [f for f in os.listdir(VIDEO_SAMPLES_DIR) 
                  if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
    
    if not video_files:
        print("  No video files found in the samples directory!")
        print("  Please add some video files to:")
        print(f"  {os.path.abspath(VIDEO_SAMPLES_DIR)}")
    else:
        for i, video in enumerate(video_files, 1):
            print(f"  {i}. {video}")
    
    print("\nServer is running. Press Ctrl+C to stop.")
    print("-" * 50)
    
    # Start the WebSocket server
    start_server = websockets.serve(
        mock_analysis, 
        "0.0.0.0", 
        WS_PORT,
        ping_interval=20,
        ping_timeout=20,
        close_timeout=10
    )
    
    try:
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("Server stopped")
