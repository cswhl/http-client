#!/usr/bin/python3


import sys
import re
import socket
import unittest
from urllib.parse import urlparse
from http.client import HTTP_PORT, HTTPS_PORT
from urllib.error import URLError


class RecvErr(Exception):
    pass


class HttpConst(object):
    '''常量类'''

    CRLF = '\r\n'
    CR = 13
    LF = 10
    # keep space, for split
    GET = 'GET '
    POST = 'POST '
    HOST = 'Host: '


def validate_url(argv):
    '''判断url是否合法'''

    if len(argv) != 2:
        print(sys.stderr, 'URL Required')
        sys.exit(-1)

    url = argv[1]
    if not re.match(r'^https?:/{2}\w.+$', url):
        print('url地址不合法')
        raise URLError('URL is unavailable')
    return True


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

    @property
    def request_packet(self):  # noqa
        '''拼接http请求'''

        request = ''

        # constructor rquest line
        request += HttpConst.GET + self.path + ' ' + 'HTTP/1.1' + ' '
        request += HttpConst.CRLF

        # header
        request += HttpConst.HOST + self.host
        request += HttpConst.CRLF

        # space line
        request += HttpConst.CRLF

        # body

        return request


class HttpClient(object):
    '''客户端'''

    def __init__(self, url: HttpURL):
        self.sock = socket.socket()
        self.sock.settimeout(3)
        try:
            addresses = url.host, url.port
            self.sock.connect(addresses)
        except socket.error as ret:
            print(f'web服务器地址错误{ret}')
            sys.exit(-1)
        self.url = url

    def __send(self):
        '''发送http报文请求'''
        request = Request(self.sock, self.url.request_packet)
        request.send_request()

    def __recv(self):
        '''接受http报文响应'''
        try:
            response = Response(self.sock)
            response.get_all()
            print(response.head)
            print(response.body)
        except RecvErr as res:
            print(f'client.recv错误--{res}')

    def run(self):
        self.__send()
        self.__recv()


class Request(object):
    '''报文请求'''

    def __init__(self, sock, http_request: str):
        self.sock = sock
        self.http_request = http_request

    def send_request(self):
        # 发送一般请求
        self.sock.send(self.http_request.encode('utf-8'))

    def redirect_request(self):
        # 重定位请求
        pass

    def https_request(self):
        # https请求, 带ssl
        pass


class Response(object):
    '''处理响应的报文'''

    def __init__(self, sock):
        self.sock = sock
        # 获取响应报文的首帧数据
        try:
            rev = self.sock.recv(1024).decode('utf-8')
            self.head, self.body = rev.split('\r\n\r\n')
            self.header_lines = self.head.split('\r\n')
        except socket.error as res:
            print(f'报文响应接受数据错误:{res}')
            raise RecvErr('接受数据错误')
        except BaseException as res:
            print(f'报文响应实例初始化时错误:{res}')
            raise RecvErr('接受数据错误')

    def get_all(self):
        self.get_line()
        self.get_header_map()
        self.get_body()

    def get_line(self):
        # 获取响应行
        self.request_line = self.header_lines[0]

    def get_header_map(self):
        # 获取响应头对应的map
        header_map = {}
        for header in self.header_lines[1:]:
            if ';' in header:
                # 处理多个消息头共处一行的情况
                headers = header.split(';')
                for header in headers:
                    cc = header.strip().split(': ') if ':' in header else header.strip().split('=')  # noqa
                    header_map.update([cc])
                continue
            header_map.update([header.split(': ')])
        self.header_map = header_map

    def get_body(self):
        # 获取响应体
        content_length = int(self.header_map.get('Content-Length', 0))
        if content_length:
            self._read_content_length(content_length)
        else:
            self._read_chunker()

    def _read_content_length(self, content_length):
        # 获取content-Length响应体
        body_length = len(self.body)
        while body_length < content_length:
            try:
                rev = self.sock.recv(1024).decode('utf-8')
            except socket.timeout as res:
                print(f'sock.recv接受数据超时---"Error:{res}"')  # noqa
            self.body += rev
            body_length += len(rev)

    def _read_chunker(self):
        # 获取分块编码形式的响应体
        pass


class TestUrl(unittest.TestCase):
    '''测试用例'''
    url = 'https://httpbin.org/'
    result = 'GET / HTTP/1.1 \r\nHost: httpbin.org\r\n\r\n'

    def test_validate_url(self):
        '''1 测试validate_url函数'''
        self.assertTrue(validate_url(['', self.url]))
        self.assertRaises(URLError, validate_url, ['', '://docs.pyhton/'])
        self.assertRaises(SystemExit, validate_url, [''])

    def test_HttpURL(self):
        '''2 测试URL构造对象'''
        url = HttpURL(self.url)
        self.assertEqual(url.protocol, 'https')
        self.assertEqual(url.path, '/')
        self.assertEqual(url.host, 'httpbin.org')
        self.assertEqual(url.port, HTTPS_PORT)

    def test_request_packet(self):
        '''3 测试url拼接'''
        url = HttpURL(self.url)
        self.assertEqual(url.request_packet, self.result)

    def test_client(self):
        '''4 测试http客户端创建'''
        self.assertRaises(SystemExit, HttpClient, ('httpbin.or', 443))
        client = HttpClient(('httpbin.org', 80))
        self.assertIsInstance(client, HttpClient)
        client.sock.close()

    def tearDown(self):
        pass


def main():
    if validate_url(sys.argv):
        url = HttpURL(sys.argv[-1])
        client = HttpClient(url)
        client.run()


if __name__ == '__main__':
    # unittest.main()
    main()
