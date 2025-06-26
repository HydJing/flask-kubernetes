from flask import Flask
from . import extensions
from .routes import auth_routes, upload_routes, download_routes, health_routes

def create_app():
    app = Flask(__name__)

    app.config["MONGO_URI_VIDEO"] = "mongodb://host.minikube.internal:27017/videos"
    app.config["MONGO_URI_MP3"] = "mongodb://host.minikube.internal:27017/mp3s"

    # Initialize MongoDB, GridFS, RabbitMQ
    extensions.init_extensions(app)

    # Register blueprints
    app.register_blueprint(health_routes.health_bp)
    app.register_blueprint(auth_routes.auth_bp)
    app.register_blueprint(upload_routes.upload_bp)
    app.register_blueprint(download_routes.download_bp)

    return app
