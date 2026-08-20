FROM python:3.11-slim

LABEL maintainer="Projeto Nimbus" \
      description="Pipeline de dados bancaria, baseada em Data Contracts, com arquitetura medallion"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl libgomp1 netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install "prefect>=2.19.0"

COPY . .

RUN mkdir -p data/landing data/processed data/gold data/quarantine \
             data/contracts data/metrics data/reports data/landing/_archive

RUN chmod +x scripts/entrypoint.sh

EXPOSE 4200

ENTRYPOINT ["scripts/entrypoint.sh"]
