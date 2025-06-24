# Use a Python 3.10 slim-buster base image
FROM python:3.10

# Set locale for Python to avoid encoding issues (using preferred 'key=value' format)
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install system dependencies for mysqlclient, curl, and pkg-config
# build-essential for general compilation tools.
# default-libmysqlclient-dev for MySQL client libraries.
# pkg-config is essential for mysqlclient to find its dependencies during build.
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv using pip
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files and lock file
# IMPORTANT: Ensure your uv.lock file is generated using Python 3.10 for consistency!
COPY pyproject.toml .
COPY uv.lock .

# Synchronize dependencies using uv sync (this command will create the .venv)
# --mount=type=cache,target=/root/.cache/uv: Caches uv's downloads/builds for faster subsequent builds.
# --mount=type=bind,source=uv.lock,target=uv.lock: Binds the uv.lock file to the build context.
# --mount=type=bind,source=pyproject.toml,target=pyproject.toml: Binds pyproject.toml.
# --locked: Installs dependencies strictly from uv.lock.
# --no-install-project: Prevents uv from installing your project itself as a package into the venv.
#                       This is typically desired for Flask apps where you just run the main script.
# --no-dev: Excludes development dependencies from the installation.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy the rest of your application code
# This should be done AFTER dependency installation to leverage Docker's layer caching.
COPY . .

# Expose Flask port
EXPOSE 5000

# Run the app using the python executable from the virtual environment
CMD [".venv/bin/python", "main.py"]