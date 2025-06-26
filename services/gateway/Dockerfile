FROM python:3.10-slim

WORKDIR /app

# Install uv
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    build-essential \
    curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv

COPY pyproject.toml ./
RUN uv venv && uv pip install --group dev

COPY . .

EXPOSE 5002
CMD ["python", "main.py"]
