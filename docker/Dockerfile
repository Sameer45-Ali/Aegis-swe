FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends git build-essential curl && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 aegisuser
WORKDIR /workspace
RUN chown -R aegisuser:aegisuser /workspace
USER aegisuser
RUN pip install --no-cache-dir pytest pytest-cov coverage
ENV PYTHONPATH=/workspace
CMD [" pytest\]
