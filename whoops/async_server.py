import socket


from .ioloop import IOLoop, Transport


class Acceptor(object):
    def __init__(self):
        # single thread accept socket
        self.accept_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.accept_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.accept_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.accept_socket.setblocking(False)

        # ioloop
        self.ioloop = None

    def transport(self):
        self.transport = Transport(self.accept_socket, self.address)
        self.transport.on_connection_cb = self.on_accept_callback
        return self.transport

    def on_accept_callback(self, conn):
        try:
            while True:
                conn, address = self.accept()
                conn.setblocking(False)
                self.ioloop.register(conn.fileno(), IOLoop._READ | IOLoop._EPOLLET)
                transport = Transport(conn, address)
                transport.events = IOLoop._READ
                transport.on_connection_cb = self.ioloop.on_connection_cb
                transport.on_write_cb = self.ioloop.on_write_cb
                transport.on_close_cb = self.ioloop.on_close_cb
                transport.connection_made_cb = self.ioloop.connection_made_cb
                self.ioloop.connections[conn.fileno()] = transport
                # connection_made callback
                self.ioloop.executor.submit(transport.connection_made_cb)
        except socket.error:
            pass

    def fileno(self):
        return self.accept_socket.fileno()

    def bind(self, address):
        self.address = address
        self.accept_socket.bind(address)

    def accept(self):
        return self.accept_socket.accept()

    def listen(self, backlog):
        self.accept_socket.listen(backlog)

    def close(self):
        self.accept_socket.close()


class AsyncServer(object):
    def __init__(self, ioloop, address):
        self.ioloop = ioloop

        # acceptor include a listened socket file.
        self.acceptor = Acceptor()
        self.acceptor.bind(address)
        # register
        self.ioloop.register_acceptor(self.acceptor)

        # register ioloop callbacks
        self.ioloop.on_connection_cb = self.on_connection
        self.ioloop.connection_made = self.connection_made
        self.ioloop.on_write_cb = self.on_write
        self.ioloop.on_close_cb = self.on_close

    def listen(self, backlog=1):
        # backlog
        self.ioloop.acceptor.listen(backlog)
        self.ioloop.start()

    def connection_made(self):
        raise NotImplementedError()

    def on_connection(self, conn):
        raise NotImplementedError()

    def on_write(self, conn):
        raise NotImplementedError()

    def on_close(self):
        raise NotImplementedError()
