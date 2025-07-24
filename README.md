# Eagle Vision Task - Scooper-Usage Violation Detection System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A microservices-based Computer Vision system to monitor hygiene compliance in food preparation areas by detecting proper scooper usage when handling ingredients.

## Features

- Real-time video analysis for scooper usage detection
- Multiple worker tracking with individual violation logging
- Configurable Regions of Interest (ROIs) for different work areas
- Web-based dashboard for monitoring and alerts
- Scalable microservices architecture

## Tech Stack

- **Backend**: Python, FastAPI, OpenCV, YOLOv8
- **Frontend**: React.js, WebSocket for real-time updates
- **Message Broker**: Kafka (with Zookeeper)
- **Database**: MongoDB for violation logging
- **Containerization**: Docker & Docker Compose

## Project Structure

```
EagleVisionTask/
├── ingestion/         # Video stream ingestion service
├── detection/         # Object detection service
├── tracking/          # Object tracking and analysis
├── violation/         # Violation processing and logging
├── frontend/          # React-based web interface
├── common/            # Shared utilities and models
├── docker/            # Docker configuration files
├── data/              # Sample data and models
├── .gitignore
├── docker-compose.yml
├── README.md
└── requirements.txt
```

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Node.js 16+ (for frontend development)
- Python 3.9+ (for local development)

## Getting Started

### Quick Start with Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/EagleVisionTask.git
   cd EagleVisionTask
   ```

2. Start all services:
   ```bash
   docker-compose up -d
   ```

3. Access the web interface at `http://localhost:3000`

### Local Development

1. Set up a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

4. Start the frontend development server:
   ```bash
   npm run dev
   ```

5. Start the backend services (in separate terminals):
   ```bash
   # Start Kafka and Zookeeper
   docker-compose -f docker-compose.kafka.yml up -d
   
   # Start backend services
   python -m ingestion.service
   python -m detection.service
   # ... and so on for other services
   ```

## Configuration

Create a `.env` file in the project root with the following variables:

```env
# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_RAW_FRAMES=raw-frames
KAFKA_TOPIC_DETECTIONS=detections
KAFKA_TOPIC_VIOLATIONS=violations

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=eagle_vision

# WebSocket
WEBSOCKET_URL=ws://localhost:8004/ws
```

## API Documentation

Once the services are running, access the API documentation at:
- `http://localhost:8000/docs` (FastAPI Swagger UI)
- `http://localhost:8000/redoc` (ReDoc)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
