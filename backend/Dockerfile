FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5001

STOPSIGNAL SIGTERM

# Exec form ensures Python is PID 1 and receives SIGTERM directly
CMD ["python", "run.py"]
