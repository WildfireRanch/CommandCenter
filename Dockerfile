# Baseimage
FROM python:3.11-slim

# Update Packages
RUN apt update && apt upgrade -y
RUN pip install --upgrade pip

# Create app directory
WORKDIR /app

# Install requirements
COPY ./railway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy railway app
COPY ./railway .

# Expose port (Railway will override with PORT env var)
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
