from fastapi import FastAPI
import threading
import uvicorn
import socket
import json
import time

socketHost = 'localhost'
socketPort = 8088
appsl = FastAPI()
server = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
socket_conns = {}

# region - TCP Connections

def tcp_conn(client_socket, address): # TCP connection daemon thread
    while True:
        try:
            recv_data = client_socket.recv(2048).decode()
            json_data = json.loads(recv_data)
            match json_data['type']:
                case 'coltroller': # Received TCP request from controller
                    controller_cmd(client_socket,json_data['content'])
                case 'client': # Received TCP request from client
                    client_msg(json_data['content'],address)
        except:
            print(end='')


def listen_tcp():
    while True:
        client_socket,address = server.accept() # Accept TCP connection
        print('Connection ' + str(address)) # Print connection base info
        socket_conns[str(address)] = client_socket # add connection to dic
        threading.Thread(target=tcp_conn,args=(client_socket,address),daemon=True).start()

# endregion

# region - WebAPI

@appsl.get("/")
def server_version():
    return { 'Server-Version': '0.1' }


@appsl.get("/list/")
def list_connections():
    return str(socket_conns)


@appsl.get("/hello/{conn_address}")
def print_hello(conn_address):
    webcoltrol = socket_conns[conn_address]
    webcoltrol.send(json.dumps({
        'type': 'coltroller',
        'content': 'hello'
    }).encode())

#endregion

def controller_cmd(client_socket,cmd):
    match cmd:
        case 'getsysinfo':
            print()
        case 'listfile':
            print()
        case 'hello':
            client_socket.send(json.dumps({
                'content': 'hello'
            }).encode())


def client_msg(msg,address):
    print(msg, end=' ')
    print(address)

#region - Heartbeat check alive

def client_heartbeat():
    while True:
        for key in list(socket_conns.keys()):
            try:
                heartbeat = socket_conns[key]
                heartbeat.send(json.dumps({
                    'type': 'heartbeat'
                }).encode())
                recv_data = heartbeat.recv(2048).decode()
                json_data = json.dumps(recv_data)
                if json_data['content'] != 'alive':
                    print("Undefind " + key)
                    socket_conns.pop(key)
            except:
                print("Undefind " + key)
                socket_conns.pop(key)
        time.sleep(1)

# endregion

# region - Run service in thread

def fastapi(): # fastapi service
    uvicorn.run(appsl, host='0.0.0.0', port=8090)


def tcplistener(): # socket tcp service
    server.bind((socketHost, socketPort))
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.listen(128)
    print("\033[0;32msocket listen on\033[0m" + ": " + socketHost + ":" + str(socketPort))
    listen_tcp()

# endregion

if __name__ == "__main__":
    fastAPI = threading.Thread(target=fastapi).start()
    tcpListener = threading.Thread(target=tcplistener).start()
    heartbeat = threading.Thread(target=client_heartbeat).start()
