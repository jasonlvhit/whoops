import sys

from io import BytesIO

from http_server import HttpServer
from whoops import ioloop


class WSGIServer(HttpServer):

    def __init__(self, ioloop, address):
        super(WSGIServer, self).__init__(ioloop, address)
        self.app = None
        self.environ = None
        self.result = None
        self.cgi_environ = None
        self.http_version = "HTTP/1.1"
        self.wsgi_version = (1, 0)
        self.wsgi_multithread = True
        self.wsgi_multiprocess = False
        self.wsgi_run_once = False

    def set_app(self, app):
        self.app = app

    def on_connection(self, conn):
        self.connection = conn
        self.parse_request()
        self.setup_environ()
        self.result = self.app(self.environ, self.start_response)
        self.finish_response()

    def setup_cgi_environ(self):
        env = {}

        request_line = self.raw_requestline.decode('latin-1').rstrip('\r\n')
        method, path, version = request_line.split(' ')

        if '?' in path:
            _path, query_string = path.split('?')
            env['QUERY_STRING'] = query_string

        env['REQUEST_METHOD'] = method
        env['PATH_INFO'] = path
        env['SERVER_PROTOCOL'] = self.http_version
        env['SERVER_HOST'] = self.host
        env['SERVER_PORT'] = self.port

        if "content-type" in self.header:
            env['CONTENT_TYPE'] = self.header.get('content-type')
        if "content-length" in self.header:
            env['CONTENT_LENGTH'] = self.header.get('content-length')

        for key, value in self.header.items():
            env["HTTP_" + key.replace("-", "_").upper()] = value

        self.cgi_environ = env

    def setup_environ(self):
        self.setup_cgi_environ()

        env = self.environ = self.cgi_environ.copy()
        env['wsgi.input'] = BytesIO(self.request_body)
        env['wsgi.errors'] = sys.stdout
        env['wsgi.version'] = self.wsgi_version
        env['wsgi.run_once'] = self.wsgi_run_once
        env['wsgi.url_scheme'] = 'http'
        env['wsgi.multithread'] = self.wsgi_multithread
        env['wsgi.wsgi_multiprocess'] = self.wsgi_multiprocess

    def start_response(self, status, headers, exc_info=None):

        code = int(status[0:3])
        message = str(status[4:])
        self.send_response(code, message)
        self.ioloop.logger.info(
            self.cgi_environ['PATH_INFO'] + "  %s %d %s" % ('HTTP/1.1', code, message))
        self.need_content_length = True
        for name, val in headers:
            if name == 'Content-Length':
                self.need_content_length = False
            self.send_header(name, val)

    def finish_response(self):
        if self.need_content_length:
            content_length = 0
            for data in self.result:
                content_length += len(data)
            self.send_header('Content-Length', content_length)

        self.end_headers()
        for data in self.result:
            self.send(data)


def make_server(host, port, app):
    server = WSGIServer(ioloop.IOLoop.instance(num_backends=1000),
                        (host, port))
    server.set_app(app)
    return server
