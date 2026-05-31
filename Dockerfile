FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências de sistema: cairo/pango (cairosvg) e ghostscript (CMYK).
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    ghostscript \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 3006

# 1 worker: o registro de jobs é em memória (app/jobs.py). Com 2+ workers o
# polling de /jobs/<id> cai em outro processo e dá 404. Concorrência fica por
# conta das threads; a geração roda em thread de background.
CMD ["gunicorn", "--bind", "0.0.0.0:3006", "app.wsgi:app", "--workers=1", "--threads=8", "--timeout=120"]
