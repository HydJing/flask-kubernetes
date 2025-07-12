import os
import sys
import logging
from dotenv import load_dotenv
from app.worker import start_worker

load_dotenv()  # Loads .env for local dev/testing

# Configure basic logging for the app (ensure this is done once, early)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    start_worker()
