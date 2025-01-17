class ServiceRegistry:

    def __init__(self):
        self.registry = dict()

    def register_service(name: str, ip: str, port: int) -> None:
        if name in self.registry:
            