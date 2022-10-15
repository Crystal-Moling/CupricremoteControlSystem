import socket
import json
import time

def tcpClient(client):
    while True:
        try:
            recv_data = client.recv(2048).decode()
            json_data = json.loads(recv_data)
            match json_data['type']:
                case 'heartbeat':
                    client.send(json.dumps({
                        'content': 'alive'
                    }).encode())
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
        tcpClient(client)
    except:
        time.sleep(1)
        connect()


if __name__ == '__main__':
    connect()
