import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import json
import time
from datetime import datetime, UTC

from common.model_definition import ModelDefinition
from common.scenario import Scenario
from common.result_message import ResultMessage
from common.rabbitmq_connection import RabbitMQConnection


class ModelExecutor:
    def __init__(self, model: ModelDefinition):
        self.model = model

    def execute(self, scenario: Scenario) -> float:
        local_vars = dict(scenario.values)
        result = eval(self.model.function, {"__builtins__": {}}, local_vars)
        return float(result)


class Worker:
    def __init__(self, worker_id: str, host: str = "localhost"):
        self.worker_id = worker_id
        self.connection = RabbitMQConnection(host=host)
        self.model = None
        self.executor = None

    def setup(self) -> None:
        self.connection.connect()
        ch = self.connection.channel
        ch.queue_declare(queue="model_queue", durable=True)
        ch.queue_declare(queue="scenario_queue", durable=True)
        ch.queue_declare(queue="result_queue", durable=True)
        print(f"Worker {self.worker_id} conectado a RabbitMQ")

    def load_model_once(self) -> bool:
        ch = self.connection.channel
        method_frame, header_frame, body = ch.basic_get(queue="model_queue", auto_ack=True)
        if body is None:
            return False
        data = json.loads(body.decode("utf-8"))
        self.model = ModelDefinition.from_dict(data)
        self.executor = ModelExecutor(self.model)
        print(f"Worker {self.worker_id} cargó modelo: {self.model.model_name} v{self.model.version}")
        return True

    def wait_for_model(self) -> None:
        while self.model is None:
            ok = self.load_model_once()
            if ok:
                break
            print(f"Worker {self.worker_id} esperando modelo...")
            time.sleep(1.0)

    def process_scenario(self, body: bytes) -> None:
        ch = self.connection.channel
        data = json.loads(body.decode("utf-8"))
        scenario = Scenario.from_dict(data)
        if self.model is None:
            print(f"Worker {self.worker_id} ignoró escenario {scenario.scenario_id}, no hay modelo cargado")
            return
        if scenario.model_version != self.model.version:
            print(f"Worker {self.worker_id} ignoró escenario {scenario.scenario_id}, version {scenario.model_version} distinta a {self.model.version}")
            return
        value = self.executor.execute(scenario)
        timestamp = datetime.now(UTC).isoformat()
        result = ResultMessage(
            scenario_id=scenario.scenario_id,
            model_version=scenario.model_version,
            worker_id=self.worker_id,
            result=value,
            timestamp=timestamp,
        )
        payload = json.dumps(result.to_dict()).encode("utf-8")
        ch.basic_publish(
            exchange="",
            routing_key="result_queue",
            body=payload,
            properties=None,
        )
        print(f"Worker {self.worker_id} procesó escenario {scenario.scenario_id} resultado={value}")

    def run(self) -> None:
        self.setup()
        self.wait_for_model()
        ch = self.connection.channel
        print(f"Worker {self.worker_id} esperando escenarios...")
        while True:
            method_frame, header_frame, body = ch.basic_get(queue="scenario_queue", auto_ack=True)
            if body is None:
                time.sleep(0.2)
                continue
            self.process_scenario(body)

    def close(self) -> None:
        self.connection.close()


if __name__ == "__main__":
    import sys
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "worker-1"
    host = sys.argv[2] if len(sys.argv) > 2 else "localhost"
    worker = Worker(worker_id=worker_id, host=host)
    try:
        worker.run()
    except KeyboardInterrupt:
        worker.close()
        print(f"Worker {worker_id} detenido")
