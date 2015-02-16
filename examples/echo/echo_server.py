from whoops import ioloop, async_server


class EchoServer(async_server.AsyncServer):

    def on_connection(self, conn):
        data = conn.read()
        print(data.decode('utf-8'))
        conn.write(data)

if __name__ == "__main__":
    EchoServer(ioloop.IOLoop.instance(num_backends=1000),
    ('127.0.0.1', 8888)).listen()
