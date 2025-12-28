FROM python:3.11-slim

# ---- System ----
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ---- User (Security!) ----
RUN useradd -m appuser

# ---- Dependencies ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- App Code ----
COPY . .

# ---- Media Dir ----
RUN mkdir -p /app/media && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# ---- Start ----
CMD ["gunicorn", "-w", "2", "-k", "gthread", "--threads", "4", "-b", "0.0.0.0:8000", "wsgi:app"]
