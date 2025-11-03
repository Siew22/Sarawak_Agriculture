# Dockerfile

# Stage 1: Define the base image
# Using python:3.10-slim for a smaller, more secure base
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies if needed in the future
# For example, OpenCV might need some libraries:
# RUN apt-get update && apt-get install -y --no-install-recommends libgl1-mesa-glx

# Copy the requirements file first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
# This will respect the .dockerignore file
COPY . /app

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
# This is the command that starts our FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
