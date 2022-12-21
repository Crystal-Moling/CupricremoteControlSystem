import codecs
import socket
import json

server = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
server.bind(('localhost', 8088))
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.listen(128)
print('\033[0;32mINFO\033[0m' + ':     Socket listen on localhost:8088')
while True:
        client_socket,address = server.accept() # Accept TCP connection
        recv_data = client_socket.recv(2048)[1:-1]
        for i in range(0,2):
            recv_data = codecs.escape_decode(recv_data)[0].decode('utf-8')
        print(recv_data)
        json_data = json.loads(recv_data)
        print(json_data)