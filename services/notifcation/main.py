from app.consumer import start_consumer

if __name__ == "__main__":
    try:
        start_consumer()
    except KeyboardInterrupt:
        print("Interrupted")
        exit(0)
