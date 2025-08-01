import pika, os
from app.notifier import send_notification


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
MP3_QUEUE = os.getenv("MP3_QUEUE", "mp3")

def start_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    def callback(ch, method, properties, body):
        print("Received message")
        err = send_notification(body)
        if err:
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=MP3_QUEUE, on_message_callback=callback)
    print("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()
