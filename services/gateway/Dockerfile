# Use a Python 3.10 slim-buster base image
FROM python:3.10-slim

# Set locale for Python to avoid encoding issues (using preferred 'key=value' format)
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install system dependencies for mysqlclient, curl, and pkg-config
# build-essential for general compilation tools.
# default-libmysqlclient-dev for MySQL client libraries.
# pkg-config is essential for mysqlclient to find its dependencies during build.
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv using pip
RUN pip install uv

# Set working directory
WORKDIR /app

# see example: https://github.com/astral-sh/uv-docker-example/blob/main/standalone.Dockerfile
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy the rest of your application code
# This should be done AFTER dependency installation to leverage Docker's layer caching.
COPY . .

# Expose Flask port
EXPOSE 8080

# Run the app using the python executable from the virtual environment
CMD [".venv/bin/python", "main.py"]
