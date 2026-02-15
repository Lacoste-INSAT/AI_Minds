FROM python:3.11-slim

WORKDIR /app

# System deps for pytesseract, PDF, audio
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python deps (context is project root, requirements is in backend/)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code — backend package
COPY backend/ ./backend/

# Ingestion observer package — needed by backend.services.ingestion
COPY ingestion/ ./ingestion/

# Agents package (prompts, etc.)
COPY agents/ ./agents/

# Create directories
RUN mkdir -p /app/data /app/config /app/watched

# Expose port (localhost only binding is done in docker-compose)
EXPOSE 8000

# Run
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
