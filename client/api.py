import random
import socket, asyncio
import json


class Server:
    host: str
    port: int
    session: socket.socket
    auth_token: str

    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def connect(self):
        self.session = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.session.connect((self.host, self.port))

    async def disconnect(self):
        obj = {
            "method": "quit"
        }
        self.session.send(json.dumps(obj).encode())
        response = json.loads(self.session.recv(2**15).decode())
        self.session.close()
        return response

    async def auth(self, login, password):
        self.session.send(json.dumps({"login": login, "password": password}).encode())
        response = json.loads(self.session.recv(2**15).decode())
        token = response["admin"]["token"]
        self.auth_token = token
        return token


server = Server("0.0.0.0", 6688)


class VCM:
    host: str
    port: int
    session: socket.socket
    auth_token: str

    def __init__(self, id, ram, cpu, disk_memory, disk_uuid):
        self.id = id
        self.ram = ram
        self.cpu = cpu
        self.disk_memory = disk_memory
        self.disk_uuid = disk_uuid

    @staticmethod
    def from_json(json):
        return VCM(json['id'], json['ram'], json['cpu'], json['disk_memory'], json['disk_uuid'])

    @staticmethod
    async def get(id):
        obj = {
            "method": "get",
            "id": id,
            "token": server.auth_token
        }
        server.session.send(json.dumps(obj).encode())
        response = json.loads(server.session.recv(2**15).decode())
        return VCM.from_json(response)

    @staticmethod
    async def add(id, ram, cpu, disk_memory, disk_uuid):
        obj = {
            "method": "add",
            "id": id,
            "ram": ram,
            "cpu": cpu,
            "disk_memory": disk_memory,
            "disk_uuid": disk_uuid,
            "token": server.auth_token
        }
        server.session.send(json.dumps(obj).encode())
        response = json.loads(server.session.recv(2 ** 15).decode())
        return VCM.from_json(response)

    @staticmethod
    async def get_disk():
        obj = {
            "method": "get_disks",
            "token": server.auth_token
        }

        server.session.send(json.dumps(obj).encode())
        response = json.loads(server.session.recv(2 ** 15).decode())
        return response

    @staticmethod
    async def statistic():
        obj = {
            "method": "statistic",
            "token": server.auth_token
        }
        server.session.send(json.dumps(obj).encode())
        response = json.loads(server.session.recv(2 ** 15).decode())
        return [VCM.from_json(el) for el in response]

    async def save(self):
        obj = {
            "method": "put",
            "id": self.id,
            "ram": self.ram,
            "cpu": self.cpu,
            "disk_memory": self.disk_memory,
            "disk_uuid": self.disk_uuid,
            "token": server.auth_token
        }
        server.session.send(json.dumps(obj).encode())
        response = json.loads(server.session.recv(2 ** 15).decode())
        return VCM.from_json(response)

    async def delete(self):
        obj = {
            "method": "delete",
            "id": self.id,
            "token": server.auth_token
        }
        server.session.send(json.dumps(obj).encode())
        response = json.loads(server.session.recv(2 ** 15).decode())
        return VCM.from_json(response)

    def json(self):
        obj = {
            "id": self.id,
            "ram": self.ram,
            "cpu": self.cpu,
            "disk_memory": self.disk_memory,
            "disk_uuid": self.disk_uuid,
        }
        return obj
