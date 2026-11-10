FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ops_platform ./ops_platform
COPY runbooks ./runbooks

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
# Keep a single worker: the background monitor runs inside each process.
CMD ["uvicorn", "ops_platform.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
