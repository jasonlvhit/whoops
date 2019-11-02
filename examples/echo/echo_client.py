from whoops import ioloop, async_client


class EchoClient(async_client.AsyncClient):
    def on_write(self, conn):
        conn.write(b"hello")
        conn.close()

    def on_connection(self, conn):
        print(conn.read())


if __name__ == "__main__":
    ioloop = ioloop.IOLoop.instance(num_backends=1000)
    client = EchoClient(ioloop, ("127.0.0.1", 8888))
    ioloop.start()
    client.connect()
