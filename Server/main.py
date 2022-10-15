from fastapi import FastAPI
import threading
import uvicorn
import socket
import json

appsl = FastAPI()
server = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
socket_conns = {}


def tcp_conn(client_socket, address):
    while True:
        recv_data = client_socket.recv(2048).decode()
        json_data = json.loads(recv_data)
        match json_data['type']:
            case 'coltroller':
                controller_cmd(client_socket,json_data['content'])
            case 'client':
                client_msg(json_data['content'],address)


def listen_tcp():
    while True:
        client_socket,address = server.accept()
        print('Connection ' + str(address))
        socket_conns[str(address)] = client_socket
        threading.Thread(target=tcp_conn,args=(client_socket,address),daemon=True).start()


def fastapi():
    uvicorn.run(appsl, host='0.0.0.0', port=8090)


def tcplistener():
    server.bind(("localhost", 8088))
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.listen(128)
    listen_tcp()


@appsl.get("/")
def read_root():
    return { 'Server-Version': '0.1' }


@appsl.get("/list/")
def list_conns():
    return json.dumps(str(socket_conns))


@appsl.get("/hello/{conn_address}")
def print_hello(conn_address):
    webcoltrol  = socket_conns[conn_address]
    webcoltrol.send(json.dumps({
        'type': 'coltroller',
        'content': 'hello'
    }).encode())


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


def client_heartbeat():
    print()


if __name__ == "__main__":
    fastAPI = threading.Thread(target=fastapi).start()
    tcpListener = threading.Thread(target=tcplistener).start()
