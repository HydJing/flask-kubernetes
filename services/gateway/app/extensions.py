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

def init_extensions(app):
    global fs_videos, fs_mp3s, channel

    # Initialize Mongo
    mongo_video.init_app(app)
    mongo_mp3.init_app(app)

    # Create GridFS objects
    fs_videos = gridfs.GridFS(mongo_video.db)
    fs_mp3s = gridfs.GridFS(mongo_mp3.db)

    try:
        # Connect to RabbitMQ once
        connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
        channel = connection.channel()
    except pika.exceptions.AMQPChannelError as e:
        print(f"Error connecting to RabbitMQ: {e}")
        