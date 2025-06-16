# Use the official Python 3.10 image as base
FROM python:3.10

# Install git-lfs for large file support
RUN apt-get update && apt-get install -y git-lfs && git lfs install

# Set the working directory
WORKDIR /app

# Copy all project files into the container
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Pull LFS files (model weights, stats, etc.)


# Expose port (change if your app uses a different port)
EXPOSE 8000

# Default command (update if you use a different entrypoint)
CMD ["gunicorn", "app:app", "--config", "gunicorn_config.py", "--timeout", "120", "--workers", "1", "--threads", "4"]
