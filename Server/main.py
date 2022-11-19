import threading
import socket
import json
import time
import os

socketHost = 'localhost'
socketPort = 8088
server = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
socket_conns = {}
conns_info = {}

class Console(threading.Thread):
    def __init__(self, conn, name):
        threading.Thread.__init__(self)
        self.connection = conn
        self.conn_name = name


    def run(self):
        while True:
            try:
                recv_data = self.connection.recv(2048).decode('utf-8')
                json_data = json.loads(recv_data)
                print('Console ' + self.conn_name + '\n - ' + str(json_data))
                self.process(self.connection, json_data)
            except:
                self.connection.close()
                print('Console ' + self.conn_name + '\n - ' + 'Connection Closed')
                raise threading.ThreadError('Connection closed')


    def process(self, conn, data):
        print(data)
        match data['type']:
            case 'list':
                conn_list = dict()
                for key in list(socket_conns.keys()):
                    conn_list[key] = conns_info[key]
                conn.send(json.dumps(conn_list).encode('utf-8'))
            case 'use':
                if data['content'] in socket_conns.keys():
                    conn.send(json.dumps({'content': 'exists'}).encode('utf-8'))
                else:
                    conn.send(json.dumps({'content': 'notexists'}).encode('utf-8'))
            case 'info':
                multipart_backward(socket_conns[data['content']], conn, json.dumps({'type': 'info'}).encode('utf-8'))
            case 'shell':
                multipart_backward(socket_conns[data['client']], conn, json.dumps({'type': 'shell', 'content': data['content']}).encode('utf-8'))
            case 'fetch':
                multipart_backward(socket_conns[data['client']], conn, json.dumps({'type': 'fetch', 'content': data['content']}).encode('utf-8'))
                socket_conns[data['client']].close()


def multipart_backward(from_client, to_client, content):
    from_client.send(content)
    key = 'NXT'
    while key == 'NXT':
        recv_bytes = from_client.recv(2048)
        json_data = json.loads(recv_bytes.decode('utf-8'))
        to_client.send(recv_bytes)
        key = json_data['key']

def tcplistener(): # socket tcp service
    server.bind((socketHost, socketPort))
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.listen(128)
    print('\033[0;32mINFO\033[0m' + ':     Socket listen on ' + socketHost + ':' + str(socketPort))
    while True:
        client_socket,address = server.accept() # Accept TCP connection
        conn_name = address[0] + ':' + str(address[1])
        recv_data = client_socket.recv(2048).decode('utf-8')
        try:
            json_data = json.loads(recv_data)
            print('Connection ' + conn_name + '\n - ' + str(json_data)) # Print connection base info
            if json_data['type'] == 'client':
                socket_conns[conn_name] = client_socket # add connection to dic
                conns_info[conn_name] = json_data['content']
            elif json_data['type'] == 'console_chk':
                client_socket.send(json.dumps({'type': 'accept'}).encode('utf-8'))
                Console(client_socket, conn_name).start()
        except json.JSONDecodeError:
            client_socket.close()


def client_heartbeat():
    while True:
        for key in list(socket_conns.keys()):
            try:
                heartbeat = socket_conns[key]
                heartbeat.send(json.dumps({
                    'type': 'heartbeat'
                }).encode())
            except socket.error as e:
                print('Connection lost ' + key + '\n - ' + e.strerror)
                socket_conns[key].close()
                socket_conns.pop(key)
        time.sleep(1)


if __name__ == "__main__":
    if not os.path.exists(os.getcwd() + os.path.sep + 'temp'): os.mkdir(os.getcwd() + os.path.sep + 'temp')
    tcpListener = threading.Thread(target=tcplistener, name='TCPListener').start()
    heartbeat = threading.Thread(target=client_heartbeat, name='HeartBeat').start()
