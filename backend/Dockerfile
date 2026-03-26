FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY scripts/ ./scripts/
COPY gtm_scenarios/ ./gtm_scenarios/
COPY gtm_seed_data/ ./gtm_seed_data/
COPY llm_client.py .
COPY demo_app.py .
COPY run.py .

ENV PORT=5001
EXPOSE 5001

CMD ["python", "run.py"]
