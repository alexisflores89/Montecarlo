import json
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class VariableDefinition:
    name: str
    dist: str
    params: Dict[str, Any]


@dataclass
class ModelDefinition:
    model_name: str
    version: int
    num_scenarios: int
    variables: List[VariableDefinition]
    function: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ModelDefinition":
        variables = [
            VariableDefinition(
                name=v["name"],
                dist=v["dist"],
                params=v.get("params", {}),
            )
            for v in data.get("variables", [])
        ]
        return ModelDefinition(
            model_name=data["model_name"],
            version=data["version"],
            num_scenarios=data["num_scenarios"],
            variables=variables,
            function=data["function"],
        )

    @staticmethod
    def from_json_file(path: str) -> "ModelDefinition":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ModelDefinition.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "version": self.version,
            "num_scenarios": self.num_scenarios,
            "variables": [
                {"name": v.name, "dist": v.dist, "params": v.params}
                for v in self.variables
            ],
            "function": self.function,
        }
