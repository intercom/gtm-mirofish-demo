FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml ./
RUN uv sync

COPY . .

ENV PORT=5001

CMD ["sh", "-c", "FLASK_PORT=${PORT} uv run python run.py"]
