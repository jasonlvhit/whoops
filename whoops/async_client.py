import socket

from .ioloop import IOLoop, Transport


class Connector(object):

    def __init__(self, remote):
        # connect socket file
        self.connect_socket = socket.create_connection(
            address=remote, timeout=30)
        self.connect_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connect_socket.setsockopt(
            socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.connect_socket.setblocking(False)

        # ioloop
        self.ioloop = None

        # remote server/client address
        self.remote = remote

        # transport
        self.transport = Transport(self.connect_socket, self.remote)
        self.transport.events = (
            IOLoop._EPOLLIN | IOLoop._EPOLLOUT | IOLoop._EPOLLERR | IOLoop._EPOLLET)

    def connect(self):
        self.connect_socket.connect(self.remote)

    def close(self):
        self.connect_socket.close()

    def fileno(self):
        return self.connect_socket.fileno()


class AsyncClient(object):

    def __init__(self, ioloop, remote):
        self.ioloop = ioloop

        self.connector = Connector(remote=remote)

        # register
        self.ioloop.register_connector(self.connector)

        # register ioloop callbacks
        self.connector.transport.on_connection_cb = self.on_connection
        self.connector.transport.connection_made = self.connection_made
        self.connector.transport.on_write_cb = self.on_write
        self.connector.transport.on_close_cb = self.on_close

    def connect(self):
        self.connector.connect()

    def shutdown(self):
        self.connector.close()
        self.ioloop.stop()

    def connection_made(self):
        raise NotImplementedError()

    def on_connection(self, conn):
        raise NotImplementedError()

    def on_write(self, conn):
        raise NotImplementedError()

    def on_close(self):
        raise NotImplementedError()


class EchoClient(AsyncClient):

    """Echo client example.

    """

    def on_write(self, conn):
        conn.write("hello from client")

    def on_connection(self, conn):
        print(conn.read())


if __name__ == '__main__':
    ioloop = IOLoop.instance(num_backends=1000)
    client = EchoClient(ioloop, ('127.0.0.1', 8888))
    ioloop.start()
    client.connect()
