FROM python:3.11-slim

# Install system dependencies for Pygame GUI graphics and audio
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    libsdl2-2.0-0 \
    libsdl2-dev \
    libsdl2-image-2.0-0 \
    libsdl2-image-dev \
    libsdl2-mixer-2.0-0 \
    libsdl2-mixer-dev \
    libsdl2-ttf-2.0-0 \
    libsdl2-ttf-dev \
    libx11-dev \
    x11-apps \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy game code
COPY . .

# Fallback display address
ENV DISPLAY=:0

# Command to run the application
CMD ["python", "main.py"]
