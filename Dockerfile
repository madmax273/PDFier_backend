# Use an official Python base image
FROM python:3.11-slim

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# (Optional) Install Rust only if needed for some Python packages
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the app code
COPY . .

# Expose the port (not strictly required for Render, but good practice)
EXPOSE 8000

# Use Render's $PORT in production, fall back to 8000 locally
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
