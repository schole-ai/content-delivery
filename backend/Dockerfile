# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install system dependencies needed by your app (git + OpenCV requirements)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8009
EXPOSE 8009

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run the application with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009"]
