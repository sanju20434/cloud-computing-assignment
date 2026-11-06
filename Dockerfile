
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN PIP_REQUIRE_HASHES=false pip install --no-cache-dir --no-deps --index-url https://download.pytorch.org/whl/cpu torch==2.15.0 && \
    PIP_REQUIRE_HASHES=false pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
