FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the default FastAPI port used by run_demo_server.py
EXPOSE 8765

# Run Uvicorn directly, overriding the host to 0.0.0.0 for Docker
CMD ["uvicorn", "run_demo_server:app", "--host", "0.0.0.0", "--port", "8765"]
