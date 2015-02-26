import logging

from http.client import parse_headers
from io import BytesIO

from whoops import ioloop, async_server, logger


class HTTPLogger(logger.BaseLogger):

    def __init__(self, address):
        super(HTTPLogger, self).__init__()
        self.logger = logging.getLogger('whoops http server')
        self.logger.setLevel(logging.INFO)
        self.extra.setdefault('address', address)
        self.FORMAT = '%(address)s %(asctime)-15s %(message)s'
        ch = logging.StreamHandler()
        formatter = logging.Formatter(self.FORMAT)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)


responses = {
    100: ('Continue', 'Request received, please continue'),
    101: ('Switching Protocols',
          'Switching to new protocol; obey Upgrade header'),

    200: ('OK', 'Request fulfilled, document follows'),
    201: ('Created', 'Document created, URL follows'),
    202: ('Accepted',
          'Request accepted, processing continues off-line'),
    203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
    204: ('No Content', 'Request fulfilled, nothing follows'),
    205: ('Reset Content', 'Clear input form for further input.'),
    206: ('Partial Content', 'Partial content follows.'),

    300: ('Multiple Choices',
          'Object has several resources -- see URI list'),
    301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
    302: ('Found', 'Object moved temporarily -- see URI list'),
    303: ('See Other', 'Object moved -- see Method and URL list'),
    304: ('Not Modified',
          'Document has not changed since given time'),
    305: ('Use Proxy',
          'You must use proxy specified in Location to access this '
          'resource.'),
    307: ('Temporary Redirect',
          'Object moved temporarily -- see URI list'),

    400: ('Bad Request',
          'Bad request syntax or unsupported method'),
    401: ('Unauthorized',
          'No permission -- see authorization schemes'),
    402: ('Payment Required',
          'No payment -- see charging schemes'),
    403: ('Forbidden',
          'Request forbidden -- authorization will not help'),
    404: ('Not Found', 'Nothing matches the given URI'),
    405: ('Method Not Allowed',
          'Specified method is invalid for this resource.'),
    406: ('Not Acceptable', 'URI not available in preferred format.'),
    407: ('Proxy Authentication Required', 'You must authenticate with '
          'this proxy before proceeding.'),
    408: ('Request Timeout', 'Request timed out; try again later.'),
    409: ('Conflict', 'Request conflict.'),
    410: ('Gone',
          'URI no longer exists and has been permanently removed.'),
    411: ('Length Required', 'Client must specify Content-Length.'),
    412: ('Precondition Failed', 'Precondition in headers is false.'),
    413: ('Request Entity Too Large', 'Entity is too large.'),
    414: ('Request-URI Too Long', 'URI is too long.'),
    415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
    416: ('Requested Range Not Satisfiable',
          'Cannot satisfy request range.'),
    417: ('Expectation Failed',
          'Expect condition could not be satisfied.'),
    428: ('Precondition Required',
          'The origin server requires the request to be conditional.'),
    429: ('Too Many Requests', 'The user has sent too many requests '
          'in a given amount of time ("rate limiting").'),
    431: ('Request Header Fields Too Large', 'The server is unwilling to '
          'process the request because its header fields are too large.'),

    500: ('Internal Server Error', 'Server got itself in trouble'),
    501: ('Not Implemented',
          'Server does not support this operation'),
    502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
    503: ('Service Unavailable',
          'The server cannot process the request due to a high load'),
    504: ('Gateway Timeout',
          'The gateway server did not receive a timely response'),
    505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
    511: ('Network Authentication Required',
          'The client needs to authenticate to gain network access.'),
}


class HttpServer(async_server.AsyncServer):

    def __init__(self, ioloop, address):

        super(HttpServer, self).__init__(ioloop, address)
        self.host, self.port = address
        self.rbufsize = -1
        self.wbufsize = 0
        self.rfile = None
        self.wfile = None
        self.connection = None
        self.raw_requestline = None
        self.request_body = None
        self.headers = None
        self._headers_buffer = []

        self.ioloop.logger = HTTPLogger(self.host)

    def on_connection(self, conn):
        self.connection = conn
        self.parse_request()
        self.do_response()

    def parse_request(self):
        data = self.connection.read()
        self.rfile = BytesIO(data)
        self.raw_requestline = self.rfile.readline(65537)
        self.header = parse_headers(self.rfile)
        self.request_body = self.rfile.readline(65537)

    def do_response(self):
        body = "<html><body><h2>Hello Whoops</h2></body></html>"
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.send_body(body)

    def send_response(self, code, message=None):
        # self.ioloop.logger.info("%s %d %s\r\n" % ('HTTP/1.1', code, message))
        if message is None or message == '':
            message = responses[code][0]
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

    def close(self):
        self.connection.close()

if __name__ == "__main__":
    HttpServer(ioloop.IOLoop.instance(num_backends=1000),
               ('127.0.0.1', 8888)).listen()
