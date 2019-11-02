from whoops.wsgilib.wsgi_server import make_server

HELLO_WORLD = b"Hello World!\n"


def my_app(environ, start_response):
    status = "200 OK"
    response_headers = [("Content-type", "text/plain")]
    start_response(status, response_headers)
    path = environ["PATH_INFO"]
    if path == "" or path == "/":
        return [HELLO_WORLD]
    else:
        pass


server = make_server("127.0.0.1", 5000, my_app)
server.listen()
