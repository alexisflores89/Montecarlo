import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import json
import random
from typing import Dict, Any

from common.model_definition import ModelDefinition
from common.scenario import Scenario
from common.rabbitmq_connection import RabbitMQConnection


class ScenarioGenerator:
    def __init__(self, model: ModelDefinition):
        self.model = model

    def generate_scenario(self, scenario_id: int) -> Scenario:
        values: Dict[str, Any] = {}
        for v in self.model.variables:
            if v.dist == "uniform":
                a = float(v.params.get("a", 0.0))
                b = float(v.params.get("b", 1.0))
                values[v.name] = random.uniform(a, b)
            elif v.dist == "normal":
                mu = float(v.params.get("mu", 0.0))
                sigma = float(v.params.get("sigma", 1.0))
                values[v.name] = random.gauss(mu, sigma)
        return Scenario(
            scenario_id=scenario_id,
            model_version=self.model.version,
            values=values,
        )


class Producer:
    def __init__(self, model_path: str, host: str = "localhost"):
        self.model = ModelDefinition.from_json_file(model_path)
        self.connection = RabbitMQConnection(host=host)
        self.generator = ScenarioGenerator(self.model)

    def setup(self) -> None:
        self.connection.connect()
        ch = self.connection.channel
        ch.queue_declare(queue="model_queue", durable=True)
        ch.queue_declare(queue="scenario_queue", durable=True)

    def publish_model(self, copies: int = 2) -> None:
        ch = self.connection.channel
        body = json.dumps(self.model.to_dict()).encode("utf-8")
        for _ in range(copies):
            ch.basic_publish(
                exchange="",
                routing_key="model_queue",
                body=body,
                properties=None,
            )
        print(f"Modelo publicado {copies} veces en model_queue")

    def publish_scenarios(self) -> None:
        ch = self.connection.channel
        for i in range(self.model.num_scenarios):
            scenario = self.generator.generate_scenario(i)
            body = json.dumps(scenario.to_dict()).encode("utf-8")
            ch.basic_publish(
                exchange="",
                routing_key="scenario_queue",
                body=body,
                properties=None,
            )
        print(f"{self.model.num_scenarios} escenarios publicados en scenario_queue")

    def run(self) -> None:
        self.setup()
        print("Publicando modelo")
        self.publish_model()
        print("Publicando escenarios")
        self.publish_scenarios()
        print("Listo")
        self.connection.close()


if __name__ == "__main__":
    producer = Producer(model_path="model.json", host="localhost")
    producer.run()
