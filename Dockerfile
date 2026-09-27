FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY ai_service/requirements.txt ./requirements.txt

# Install CPU-only PyTorch
RUN pip install --no-cache-dir \
    torch==2.14.0 \
    --index-url https://download.pytorch.org/whl/cpu

# Install the remaining dependencies from PyPI
RUN grep -v '^torch==' requirements.txt > requirements-no-torch.txt \
    && pip install --no-cache-dir -r requirements-no-torch.txt

# Pre-download models into the image so the container never fetches them at runtime
RUN python -c "\
from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('BAAI/bge-m3'); \
CrossEncoder('BAAI/bge-reranker-v2-m3')"

# Copy the AI service, including its data/vector store
COPY ai_service ./ai_service

ENV PORT=8080

CMD exec uvicorn ai_service.app.main:app --host 0.0.0.0 --port ${PORT}