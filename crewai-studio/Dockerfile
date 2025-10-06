# Baseimage
FROM python:3.12.10-slim-bookworm

# Update Packages
RUN apt update && apt upgrade -y
RUN pip install --upgrade pip
RUN apt-get install -y build-essential bash

# Create app directory
RUN mkdir -p /CrewAI-Studio
WORKDIR /CrewAI-Studio

# Install requirements
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Copy all files
COPY . .

# Make start.sh executable
RUN chmod +x start.sh

# Expose port (Railway will override with PORT env var)
EXPOSE 8080

# Run app using bash with explicit path
CMD ["/bin/bash", "./start.sh"]
