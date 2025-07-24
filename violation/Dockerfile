# Violation Service Dockerfile
FROM eaglevision-base:latest

WORKDIR /app

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
