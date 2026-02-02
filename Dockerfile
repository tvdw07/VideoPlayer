FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create non-root user
RUN useradd -m -u 10001 appuser

# Install deps first (better build cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Ensure writable dirs (only what you need)
RUN mkdir -p /app/media /app/instance && \
    chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

CMD ["gunicorn", "-w", "2", "-k", "gthread", "--threads", "4", "--timeout", "90", "--graceful-timeout", "30", "--access-logfile", "-", "--error-logfile", "-", "--max-requests", "2000", "--max-requests-jitter", "200", "-b", "0.0.0.0:8000", "wsgi:app"]
