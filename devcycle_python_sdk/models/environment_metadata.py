class EnvironmentMetadata:
    def __init__(
        self,
        id: str,
        key: str,
    ):
        self.id = id
        self.key = key

    @staticmethod
    def from_json(json_str: str) -> "EnvironmentMetadata":
        if json_str is None:
            return None
        return EnvironmentMetadata(
            id=json_str["id"],
            key=json_str["key"],
        )