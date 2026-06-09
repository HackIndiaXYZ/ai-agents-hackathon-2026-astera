# Use the official Python 3.10 slim image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend and frontend folders into the container
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Expose port 7860 (Standard port for Hugging Face Spaces)
EXPOSE 7860

# Command to run the application using uvicorn from the backend directory
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
