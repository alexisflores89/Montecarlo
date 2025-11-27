from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Scenario:
    scenario_id: int
    model_version: int
    values: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "model_version": self.model_version,
            "values": self.values,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Scenario":
        return Scenario(
            scenario_id=data["scenario_id"],
            model_version=data["model_version"],
            values=data["values"],
        )
