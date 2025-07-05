import os
from flask import Flask
from dotenv import load_dotenv
from . import extensions
from .routes import auth_routes, upload_routes, download_routes, health_routes

def create_app():
    load_dotenv()

    server = Flask(__name__)

    server.config["MONGO_URI_VIDEO"] = os.getenv("MONGO_URI_VIDEO").strip()
    server.config["MONGO_URI_MP3"] = os.getenv("MONGO_URI_MP3").strip()

    server.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "a_default_secret_if_not_set") # Provide a fallback
    server.config["DEBUG"] = os.getenv("DEBUG", "False").lower() == "true" # Convert string to boolean
    
    # Store RabbitMQ host in config if extensions needs it, or pass directly
    server.config["RABBITMQ_HOST"] = os.getenv("RABBITMQ_HOST", "rabbitmq") # Default to "rabbitmq"
    server.config["RABBITMQ_PORT"] = os.getenv("RABBITMQ_PORT", 5672) # Default to 5672


    # Initialize MongoDB, GridFS, RabbitMQ
    extensions.init_extensions(server)

    # Register blueprints
    server.register_blueprint(health_routes.health_bp)
    server.register_blueprint(auth_routes.auth_bp)
    server.register_blueprint(upload_routes.upload_bp)
    server.register_blueprint(download_routes.download_bp)

    return server
