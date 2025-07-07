import os, sys, json, pika, gridfs, tempfile
from pymongo import MongoClient
from bson.objectid import ObjectId
from moviepy import VideoFileClip
from dotenv import load_dotenv

load_dotenv()

def start_worker():
    try:
        print("Converter worker starting...")
        client = MongoClient(os.environ.get("MONGO_HOST", "host.minikube.internal"), 27017)
        fs_videos = gridfs.GridFS(client[os.environ.get("VIDEO_DB", "videos")])
        fs_mp3s = gridfs.GridFS(client[os.environ.get("MP3_DB", "mp3s")])

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.environ.get("RABBITMQ_HOST"), port=os.environ.get("RABBITMQ_PORT")))
        channel = connection.channel()

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
