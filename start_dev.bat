@echo off
echo Starting development environment...

REM Start the mock WebSocket server
start "Mock WebSocket Server" python mock_websocket_server.py

REM Start the frontend development server
cd frontend
start "Frontend" cmd /k "npm run dev"

echo Development environment started successfully!
pause
