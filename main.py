import os
import socket

from utils import create_http_response, reap_children, valid_path


def create_serv(port):
    server = socket.create_server(('', port))
    server.listen()
    return server


def accept_client_conn(serv, cid):
    client_sock, _ = serv.accept()
    return client_sock


def serve_client(client_sock, cid):
    child_pid = os.fork()
    if child_pid:
        client_sock.close()
        return child_pid

    data = client_sock.recv(1024).decode('utf-8')

    content = load_pade(data)
    client_sock.send(content)
    client_sock.close()


def load_pade(data):
    split = data.split(' ')

    path = '/'
    if len(split) > 1:
        path = split[1]

    path = valid_path(path)
    method = split[0]
    _, extension = os.path.splitext(path)

    is_open = False
    res_len = 0
    res = ''

    if len(path) == 0:
        return create_http_response(403, 'default', 0).encode('utf-8')

    if method != 'GET' and method != 'HEAD':
        return create_http_response(405, 'default', 0).encode('utf-8')

    if path[len(path) - 1] == '/' and len(path.split('.')) >= 2:
        return create_http_response(404, 'default', res_len).encode('utf-8')

    try:

        if method == 'GET':
            with open('.' + path, 'rb') as file:
                res = file.read()
            res_len = len(res)
            is_open = True
        else:
            res_len = os.path.getsize('.' + path)

        if is_open:
            return create_http_response(200, extension, res_len).encode('utf-8') + res
        return create_http_response(200, extension, res_len, 'close').encode('utf-8')

    except FileNotFoundError:
        if path.endswith('index.html') and len(path.split('/')) > 3:
            return create_http_response(403, 'default', 0).encode('utf-8')

        return create_http_response(404, 'default', res_len).encode('utf-8')


def run_server(port=5050):
    serv_sock = create_serv(port)
    active_children = set()
    cid = 0

    while True:
        client_sock = accept_client_conn(serv_sock, cid)
        client_pid = serve_client(client_sock, cid)
        active_children.add(client_pid)

        if cid != 0 and cid % 50 == 0:
            # close child process
            reap_children(active_children)

        cid += 1


run_server(80)