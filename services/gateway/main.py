import os
from app import create_app
from dotenv import load_dotenv

load_dotenv()  # Load env vars from .env

server = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server.run(host="0.0.0.0", port=port)
