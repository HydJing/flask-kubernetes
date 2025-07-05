import pika.exceptions
from flask_pymongo import PyMongo
import pika
import gridfs

# Mongo clients (init with app later)
mongo_video = PyMongo()
mongo_mp3 = PyMongo()

# GridFS instances (created after app is ready)
fs_videos = None
fs_mp3s = None

# RabbitMQ connection and channel (created once)
channel = None
connection = None # Store the connection object to manage its lifecycle

def init_extensions(app):
    global fs_videos, fs_mp3s, channel, connection

    mongo_video_uri = app.config.get('MONGO_URI_VIDEO')
    mongo_mp3_uri = app.config.get('MONGO_URI_MP3')

    # Explicitly pass the URI to init_app.
    # We are no longer using 'config_prefix' for the URI itself.
    mongo_video.init_app(app, uri=mongo_video_uri)
    mongo_mp3.init_app(app, uri=mongo_mp3_uri)


    # Create GridFS objects
    fs_videos = gridfs.GridFS(mongo_video.db)
    fs_mp3s = gridfs.GridFS(mongo_mp3.db)
    
    rabbitmq_host = app.config.get("RABBITMQ_HOST")
    rabbitmq_port = app.config.get("RABBITMQ_PORT")

    try:
        # Connect to RabbitMQ once
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port))
        channel = connection.channel()
        print(f"RabbitMQ connection established successfully to {rabbitmq_host}.")
    except pika.exceptions.AMQPChannelError as e:
        print(f"Failed to connect to RabbitMQ at {rabbitmq_host}: {e}")
        
    @app.teardown_appcontext
    def close_rabbitmq_connection(exception=None):
        if connection and not connection.is_closed:
            print("Closing RabbitMQ connection.")
            connection.close()