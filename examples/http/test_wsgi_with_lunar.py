from lunar.lunar import Lunar
from wsgi_server import make_server

app = Lunar(__name__)


@app.route('/')
def hello_world():
    return '<html><body>Hello World!</body></html>'

if __name__ == '__main__':
    my_app = app
    server = make_server('127.0.0.1', 5000, my_app)
    server.listen()
