FROM python:3.11-slim

WORKDIR /app

# System deps for pytesseract, PDF, audio
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# spacy is commented out in requirements.txt; skip download until enabled
# RUN python -m spacy download en_core_web_sm

# App code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose port (localhost only binding is done in docker-compose)
EXPOSE 8000

# Run
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
