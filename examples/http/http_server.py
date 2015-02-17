from http.client import parse_headers
from io import BytesIO

from whoops import ioloop, async_server


class HttpServer(async_server.AsyncServer):

    def __init__(self, ioloop, address):
        super(HttpServer, self).__init__(ioloop, address)

        self.rbufsize = -1
        self.wbufsize = 0
        self.rfile = None
        self.wfile = None
        self.connection = None
        self.raw_requestline = None
        self.headers = None
        self._headers_buffer = []

        
    def on_connection(self, conn):
        self.connection = conn
        self.parse_request()
        self.do_response()

    def parse_request(self):
        data = self.connection.read()
        self.rfile = BytesIO(data)
        self.raw_requestline = self.rfile.readline(65537)
        self.header = parse_headers(self.rfile)

    def do_response(self):
        body = "<html><body><h2>Hello Whoops</h2></body></html>"
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.send_body(body)

    def send_response(self, code, message=None):
        self._headers_buffer.append(
            ("%s %d %s\r\n" % ('HTTP/1.1', code, message)).encode('latin-1', 'strict'))
        self.send_header('Server', 'whoops/0.1')

    def send_header(self, key, value):
        self._headers_buffer.append(
            ("%s: %s\r\n" % (key, value)).encode('latin-1', 'strict'))

    def end_headers(self):
        self._headers_buffer.append(b"\r\n")
        self.flush_headers()

    def flush_headers(self):
        self.send(b''.join(self._headers_buffer))
        self._headers_buffer = []

    def send_body(self, body):
        self.send(body.encode('latin-1'))

    def send(self, msg, body=None):
        if body:
            msg += body
        self.connection.write(msg)

if __name__ == "__main__":
    HttpServer(ioloop.IOLoop.instance(num_backends=1000),
               ('127.0.0.1', 8888)).listen()
