from whoops import ioloop, async_server

class EchoServer(async_server.AsyncServer):

    def on_connection(self, conn):
        data = conn.read()
        print(data)
        conn.write(b"HTTP/1.1 200 OK\r\nServer: myhttpd/0.1.0\r\nContent-Type: text/html\r\nContent-Length: 20\r\n\r\n<html>Hello</html>\r\n")

if __name__ == "__main__":
    EchoServer(ioloop.IOLoop.instance(num_backends=1000),
    ('127.0.0.1', 8888)).listen()
