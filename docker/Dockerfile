# PolicyRAG API / UI image (CPU torch for portability; the LLM runs in the separate Ollama container,
# which is where GPU acceleration matters most).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POLICYRAG_DEVICE=cpu \
    HF_HOME=/opt/hf

WORKDIR /app

COPY requirements.txt .
RUN pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.7" \
 && pip install -r requirements.txt

# Bake the embedding + reranker weights into the image so containers start without network access.
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('BAAI/bge-small-en-v1.5'); CrossEncoder('BAAI/bge-reranker-base')"

COPY pyproject.toml README.md ./
COPY src/ src/
COPY config/ config/
COPY ui/ ui/
COPY data/raw/ data/raw/
COPY data/golden_set.json data/facts.json data/
RUN pip install --no-deps -e .

# Build the FAISS index at image build time (deterministic for a given corpus + model).
RUN python -m policyrag.ingestion.embed_and_index

RUN useradd --create-home app && mkdir -p logs reports && chown -R app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=4)"

CMD ["uvicorn", "policyrag.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
