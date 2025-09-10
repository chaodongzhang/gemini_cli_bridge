class FastMCP:
    def __init__(self, name: str):
        self.name = name

    def tool(self):
        def _decorator(func):
            return func
        return _decorator

    def run(self) -> None:
        pass

