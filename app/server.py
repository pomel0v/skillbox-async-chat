#
# Серверное приложение для соединений
#
import asyncio
import time
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    @property
    def timestamp(self):
        return time.strftime("%H:%M:%S", time.localtime())

    def data_received(self, data: bytes):
        decoded = data.decode().strip('\r\n')
        print(self.timestamp, decoded)

        if self.login is not None:
            self.send_message(decoded)

        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "")

                for client in self.server.clients:
                    if self.login == client.login and self != client:
                        self.transport.write(
                            f"{self.timestamp} Ошибка! Логин {self.login} уже занят, попробуйте другой.".encode())
                        self.transport.close()

                else:
                    self.transport.write(f"Привет, {self.login}!".encode())
                    self.send_history()

            else:
                self.transport.write("Ошибка! Сначала нужно авторизоваться. Команда login:<ваш логин>".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.timestamp} <{self.login}>: {content}"

        for user in self.server.clients:
            user.transport.write(message.encode())

        self.server.history.append(message)

    def send_history(self, n=10):
        history = self.server.history[-n:]
        self.transport.write(f"Last {n} messages:\n".encode())
        self.transport.write('\n'.join(history).encode())


class Server:
    clients: list

    def __init__(self):
        self.clients = []
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
