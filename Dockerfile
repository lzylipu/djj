FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" httpx pyyaml
COPY api/ ./api/
COPY web/ ./web/
VOLUME /videos
VOLUME /data
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8080"]
