FROM python:3.10-slim

# Install system dependencies needed for compiling mysqlclient
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (recommended: pin version for reproducibility)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set work directory
WORKDIR /app

# Copy project files
COPY . .

# Create and activate virtual environment in-project (like .venv)
RUN uv venv && . .venv/bin/activate && uv pip install --all

# Expose Flask app port
EXPOSE 5000

# Command to run Flask app
CMD [".venv/bin/python", "main.py"]
