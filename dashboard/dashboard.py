import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import json
import time
from collections import defaultdict
from typing import Dict, List

import matplotlib.pyplot as plt

from common.result_message import ResultMessage
from common.rabbitmq_connection import RabbitMQConnection


class ResultAggregator:
    def __init__(self):
        self.worker_counts: Dict[str, int] = defaultdict(int)
        self.results: List[float] = []

    def record(self, result: ResultMessage) -> None:
        self.worker_counts[result.worker_id] += 1
        self.results.append(result.result)


class Dashboard:
    def __init__(self, host: str = "localhost"):
        self.connection = RabbitMQConnection(host=host)
        self.aggregator = ResultAggregator()

    def setup(self) -> None:
        self.connection.connect()
        ch = self.connection.channel
        ch.queue_declare(queue="result_queue", durable=True)

    def fetch_results(self) -> None:
        ch = self.connection.channel
        while True:
            method_frame, header_frame, body = ch.basic_get(queue="result_queue", auto_ack=True)
            if body is None:
                break
            data = json.loads(body.decode("utf-8"))
            msg = ResultMessage.from_dict(data)
            self.aggregator.record(msg)

    def run(self) -> None:
        self.setup()
        plt.ion()
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        while True:
            self.fetch_results()
            ax1.clear()
            ax2.clear()
            workers = list(self.aggregator.worker_counts.keys())
            counts = [self.aggregator.worker_counts[w] for w in workers]
            if workers:
                ax1.bar(workers, counts)
                ax1.set_title("Escenarios procesados por worker")
            if self.aggregator.results:
                ax2.hist(self.aggregator.results, bins=20)
                ax2.set_title("Distribución de resultados")
            fig.tight_layout()
            plt.pause(0.5)
            time.sleep(0.5)


if __name__ == "__main__":
    dashboard = Dashboard(host="localhost")
    dashboard.run()
