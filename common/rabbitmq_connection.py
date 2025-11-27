import pika


class RabbitMQConnection:
    def __init__(self, host: str = "localhost", port: int = 5672, virtual_host: str = "/", username: str = "guest", password: str = "guest"):
        self.host = host
        self.port = port
        self.virtual_host = virtual_host
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None

    def connect(self) -> None:
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.virtual_host,
            credentials=credentials,
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

    def close(self) -> None:
        if self.channel is not None:
            self.channel.close()
        if self.connection is not None:
            self.connection.close()
