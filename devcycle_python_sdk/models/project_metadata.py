from typing import Dict, Any, Optional


class ProjectMetadata:
    def __init__(
        self,
        id: str,
        key: str,
    ):
        self.id = id
        self.key = key

    @staticmethod
    def from_json(json_obj: Optional[Dict[str, Any]]) -> Optional["ProjectMetadata"]:
        if json_obj is None:
            return None
        return ProjectMetadata(
            id=json_obj["id"],
            key=json_obj["key"],
        )
