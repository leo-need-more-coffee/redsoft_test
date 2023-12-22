import asyncio, socket
from typing import Callable


class Server:
    """ Сервер. Принимает сокеты и перенаправляет в хэндлер.

    Attributes:
        ip  IP.
        port  Port.
        handler Handler.
    """
    ip: str
    port: int
    handler: Callable

    def __init__(self, ip, port, handler):
        self.ip = ip
        self.port = port
        self.handler = handler

    async def run(self):
        server = await asyncio.start_server(self.handler, self.ip, self.port)
        await server.serve_forever()
