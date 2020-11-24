#!/usr/bin/python3

import socket
from urllib.parse import urlparse
from http.client import HTTP_PORT, HTTPS_PORT


class HttpURL(object):
    '''构造url对象'''

    def __init__(self, url):
        self._url = urlparse(url)

    @property
    def protocol(self):
        return self._url.scheme

    @property
    def host(self):
        return self._url.hostname

    @property
    def path(self):
        return self._url.path if self._url.path else '/'

    @property
    def port(self):
        return self._url.port if self._url.port else self._default_port(self.protocol)  # noqa

    def _default_port(self, protocol):
        return HTTP_PORT if self.protocol == 'http' else HTTPS_PORT


# 1.创建tcp套接字
# 2.创建http协议- 请求报文
# htpp请求行
# data = 'GET / HTTP/1.1\r\n'
data = 'GET / HTTP/1.1\r\n'
# http请求头
data += 'Host: httpbin.org\r\n'
# data += 'Host:www.baidu.com\r\n'
# data = 'GET /en-US/docs/Web/HTTP/Headers/Transfer-Encoding HTTP/1.1\r\n'
# data += 'Host: developer.mozilla.org\r\n'
# data += 'Transfer-Encoding: chunked\r\n'
# 空行
data += '\r\n\r\n'
# http请求体


# 样板代码
sock = socket.socket()

# port = 8888
# host = 'localhost'

# baidu
# port = 443
# host = '14.215.177.39'

# httpbin
port = 80
host = 'httpbin.org'

# ff
# port =  80
# host = 'developer.mozilla.org'

addresock = host, port
sock.settimeout(3)
sock.connect(addresock)


def head_to_map(headLines):
    # 将响应头转换字典

    header_map = {}
    for header in header_lines[1:]:
        if ';' in header:
            # 处理多个消息头共处一行的情况
            headers = header.split(';')
            for header in headers:
                cc = header.strip().split(': ') if ':' in header else header.strip().split('=')  # noqa
                header_map.update([cc])
            continue
        header_map.update([header.split(': ')])

    return header_map


def get_res_body(body, content_length):
    body_length = len(body)
    while body_length < content_length:
        try:
            rev = sock.recv(1024).decode('utf-8')
        except socket.timeout as res:
            print(f'sock.recv接受数据超时---"Error:{res}"')  # noqa
        body += rev
        body_length += len(rev)
    return body


while True:
    sock.send(data.encode('utf-8'))
    rev = sock.recv(1024).decode('utf-8')
    head, body = rev.split('\r\n\r\n')
    header_lines = head.split('\r\n')
    request_line = header_lines[0]
    header_map = head_to_map(header_lines[1:])
    content_length = int(header_map.get('Content-Length', 0))

    body = get_res_body(body, content_length)

    # print(head)
    # print(body)

    break

sock.close()  # 会向服务发送b''，服务器接收到就会关闭连接'
