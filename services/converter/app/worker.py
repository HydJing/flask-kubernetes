import os, sys, json, pika, gridfs, tempfile
from pymongo import MongoClient
from bson.objectid import ObjectId
from moviepy import VideoFileClip


def start_worker():
    try:
        print("Converter worker starting...")
        
        # Get MongoDB credentials from environment variables
        mongo_host = os.environ.get("MONGO_HOST", "mongodb-service.mongodb-service.svc.cluster.local")
        mongo_username = os.environ.get("MONGO_INITDB_ROOT_USERNAME")
        mongo_password = os.environ.get("MONGO_INITDB_ROOT_PASSWORD")
        rabbitmq_host=os.environ.get("RABBITMQ_HOST", "rabbitmq-service.rabbitmq-message.svc.cluster.local")
        rabbitmq_port=int(os.environ.get("RABBITMQ_PORT", "5672"))

        # Construct the MongoDB connection URI with authentication
        # Format: mongodb://username:password@host:port/database?authSource=admin
        # The 'admin' database is where the root user is defined.
        mongo_host = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:27017/?authSource=admin"

        # Initialize MongoClient with the full URI
        client = MongoClient(mongo_host, 27017)

        # The databases for GridFS are still taken from env vars or defaults
        fs_videos = gridfs.GridFS(client[os.environ.get("VIDEO_DB", "videos")])
        fs_mp3s = gridfs.GridFS(client[os.environ.get("MP3_DB", "mp3s")])

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port))
        channel = connection.channel()

        # Explicitly declare queues (good practice)
        channel.queue_declare(queue=os.environ.get("VIDEO_QUEUE", "video"), durable=True) 
        channel.queue_declare(queue=os.environ.get("MP3_QUEUE", "mp3"), durable=True)   

        def callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                video_fid = message["video_fid"]

                video_data = fs_videos.get(ObjectId(video_fid)).read()
                tf = tempfile.NamedTemporaryFile(delete=False)
                tf.write(video_data)
                tf.close()

                audio = VideoFileClip(tf.name).audio
                audio_path = f"/tmp/{video_fid}.mp3"
                audio.write_audiofile(audio_path)

                with open(audio_path, "rb") as f:
                    mp3_fid = fs_mp3s.put(f.read())

                os.remove(audio_path)
                os.remove(tf.name)

                message["mp3_fid"] = str(mp3_fid)
                channel.basic_publish(
                    exchange="",
                    routing_key=os.environ.get("MP3_QUEUE"),
                    body=json.dumps(message),
                    properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
                )

                ch.basic_ack(delivery_tag=method.delivery_tag)
                print(f"Converted video {video_fid} to mp3: {message['mp3_fid']}")

            except Exception as e:
                print(f"Error: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=os.environ.get("VIDEO_QUEUE", "video"), on_message_callback=callback)
        channel.start_consuming()

    except KeyboardInterrupt:
        print("Converter shutdown requested...")
        sys.exit(0)
