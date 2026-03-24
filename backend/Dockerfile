FROM python:3.11-slim
WORKDIR /app
RUN pip install flask flask-cors python-dotenv
COPY gtm_scenarios/ ./gtm_scenarios/
COPY demo_app.py .
ENV PORT=5001
CMD ["sh", "-c", "python demo_app.py"]
