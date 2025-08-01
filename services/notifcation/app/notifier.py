import smtplib
import os
import json
from email.message import EmailMessage


def send_notification(message):
    print("Raw message received:", message)

    try:
        message = json.loads(message)
        print("Parsed message:", message)

        mp3_fid = message["mp3_fid"]
        receiver_address = message["username"]

        sender_address = os.environ.get("EMAIL_SENDER_ADDRESS")
        mailjet_api_key = os.environ.get("MAILJET_API_KEY")
        mailjet_secret_key = os.environ.get("MAILJET_SECRET_KEY")

        # Validate required environment variables
        if not sender_address:
            raise EnvironmentError("Missing EMAIL_SENDER_ADDRESS")
        if not mailjet_api_key or not mailjet_secret_key:
            raise EnvironmentError("Missing MAILJET_API_KEY or MAILJET_SECRET_KEY")

        msg = EmailMessage()
        msg.set_content(f"mp3 file_id: {mp3_fid} is now ready!")
        msg["Subject"] = "MP3 Download"
        msg["From"] = sender_address
        msg["To"] = receiver_address

        print(f"Connecting to SMTP server as {mailjet_api_key}...")

        session = smtplib.SMTP("in-v3.mailjet.com", 587)
        session.set_debuglevel(1)  # Enable SMTP debug output
        session.starttls()
        session.login(mailjet_api_key, mailjet_secret_key)
        session.send_message(msg)
        session.quit()
        print("Mail Sent")

    except Exception as e:
        print("Error sending email:", e)
        raise
