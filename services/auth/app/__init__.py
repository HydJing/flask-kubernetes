import os
from flask import Flask
from flask_mysqldb import MySQL

from .routes import auth_bp

# App Factory

mysql = MySQL()

def create_app():
    app = Flask(__name__)

    # Config from environment
    app.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
    app.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
    app.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
    app.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
    app.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT"))

    mysql.init_app(app)

    # Register routes
    
    app.register_blueprint(auth_bp)

    return app
