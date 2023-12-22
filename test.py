"""
Скрипт для вручного ввода команд.
"""
import socket
import json


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = "0.0.0.0"
port = 6688
s.connect((host, port))

s.send(json.dumps({"login": "admin", "password": "admin"}).encode())
data = json.loads(s.recv(2**15).decode())
token = data["admin"]["token"]

while True:
    request = json.loads(input('enter: '))
    request['token'] = token
    s.send(json.dumps(request).encode())
    data = s.recv(2**15).decode()
    print(data)
    if 'quit' in data:
        break

s.close()
