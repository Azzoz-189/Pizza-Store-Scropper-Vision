import asyncio
import websockets
import json

async def listen():
    uri = "ws://localhost:8004/ws"
    print(f"Connecting to WebSocket at {uri}...")
    async with websockets.connect(uri) as websocket:
        print("Connected! Waiting for messages...")
        while True:
            try:
                message = await websocket.recv()
                print(f"Received message: {message}")
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed")
                break

if __name__ == "__main__":
    print("WebSocket Test Client")
    print("Press Ctrl+C to exit")
    try:
        asyncio.get_event_loop().run_until_complete(listen())
    except KeyboardInterrupt:
        print("Exiting...")
