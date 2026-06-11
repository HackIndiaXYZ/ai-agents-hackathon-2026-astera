# Use the official Python 3.10 slim image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend into the container
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Expose port 8080 (Google Cloud Run standard port)
EXPOSE 8080

# Run uvicorn from the /app directory so 'backend.main' resolves correctly
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
