from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ResultMessage:
    scenario_id: int
    model_version: int
    worker_id: str
    result: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "model_version": self.model_version,
            "worker_id": self.worker_id,
            "result": self.result,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ResultMessage":
        return ResultMessage(
            scenario_id=data["scenario_id"],
            model_version=data["model_version"],
            worker_id=data["worker_id"],
            result=data["result"],
            timestamp=data["timestamp"],
        )
