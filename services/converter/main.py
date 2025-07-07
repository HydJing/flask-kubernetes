from dotenv import load_dotenv
from app.worker import start_worker

load_dotenv()  # Loads .env for local dev/testing

if __name__ == "__main__":
    start_worker()
