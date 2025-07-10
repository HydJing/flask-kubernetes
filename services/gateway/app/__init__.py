import sys
import os
from flask import Flask
from dotenv import load_dotenv # Still here if you use .env for local dev
import logging
from . import extensions
from .routes import auth_routes, upload_routes, download_routes, health_routes

# Configure basic logging for the app (ensure this is done once, early)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

def create_app():
    load_dotenv() # For local development

    server = Flask(__name__)

    # --- App Configuration ---
    server.config["MONGO_URI_VIDEO"] = os.getenv("MONGO_URI_VIDEO", "mongodb://<mongodb_username>:<mongodb_password>@mongodb-service.mongodb-service.svc.cluster.local:27017/videos?authSource=admin").strip()
    server.config["MONGO_URI_MP3"] = os.getenv("MONGO_URI_MP3", "mongodb://<mongodb_username>:<mongodb_password>@mongodb-service.mongodb-service.svc.cluster.local:27017/mp3s?authSource=admin").strip()
    server.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "a_strong_default_secret_key_for_dev_only")
    server.config["DEBUG"] = os.getenv("DEBUG", "False").lower() == "true"
    server.config["RABBITMQ_HOST"] = os.getenv("RABBITMQ_HOST", "rabbitmq-service.default.svc.cluster.local").strip()
    server.config["RABBITMQ_PORT"] = int(os.getenv("RABBITMQ_PORT", "5672"))
    # Add queue names to app config
    server.config["VIDEO_QUEUE"] = os.getenv("VIDEO_QUEUE", "video").strip()
    server.config["MP3_QUEUE"] = os.getenv("MP3_QUEUE", "mp3").strip()


    # --- Debug: Log the loaded config values ---
    logger.info(f"App Config: MONGO_URI_VIDEO = '{server.config['MONGO_URI_VIDEO']}'")
    logger.info(f"App Config: MONGO_URI_MP3 = '{server.config['MONGO_URI_MP3']}'")
    logger.info(f"App Config: RABBITMQ_HOST = '{server.config['RABBITMQ_HOST']}'")
    logger.info(f"App Config: RABBITMQ_PORT = '{server.config['RABBITMQ_PORT']}'")
    logger.info(f"App Config: SECRET_KEY = '{server.config['SECRET_KEY']}'")
    logger.info(f"App Config: DEBUG = {server.config['DEBUG']}")
    logger.info(f"App Config: VIDEO_QUEUE = '{server.config['VIDEO_QUEUE']}'")
    logger.info(f"App Config: MP3_QUEUE = '{server.config['MP3_QUEUE']}'")


    # Initialize Flask extensions (PyMongo) and setup RabbitMQ connection management
    try:
        extensions.init_extensions(server)
        logger.info("Extensions initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize application extensions: {e}", exc_info=True)
        raise # Re-raise to crash early and visibly

    # Register blueprints
    server.register_blueprint(health_routes.health_bp)
    server.register_blueprint(auth_routes.auth_bp)
    server.register_blueprint(upload_routes.upload_bp)
    server.register_blueprint(download_routes.download_bp)

    return server