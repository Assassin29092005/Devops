# Not in the exercise: the pipeline's "Build Docker Image" stage needs a Dockerfile.
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir prometheus-client
COPY delivery_metrics.py .
EXPOSE 8000
# -u = unbuffered, so the [DEBUG]/[INFO] lines show up in `docker logs` immediately
CMD ["python", "-u", "delivery_metrics.py"]
