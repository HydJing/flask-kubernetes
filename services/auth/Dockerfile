FROM python:3.11-slim

# Set working dir
WORKDIR /app

# Install uv
RUN pip install uv

# Copy files
COPY . .

# Install dependencies
RUN uv pip install -r requirements.txt

# Expose and run
EXPOSE 5000
CMD ["uv", "pip", "run", "python", "main.py"]
