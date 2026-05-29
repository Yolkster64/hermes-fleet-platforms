FROM python:3.11-slim

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir psutil streamlit requests

ENV HERMES_CPP_NATIVE_LIB=/workspace/core/native/hermes_learning_kernel.so

CMD ["python", "core/hermes_super_orchestrator.py"]
