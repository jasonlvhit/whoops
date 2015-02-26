import socket
import select
import threading

from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

from .logger import DefaultLogger


class Transport(object):

    """ Encapsulation for connection and events.

    transport instance provide read and write methods under
    Edge Trigger(EPOLLET) mode of epoll.

    4 callbacks are bind to the connection instance:

    * `on write callback` : EPOLLOUT(_WRITE) returned.
    * `on close callback` : ERROR occur or close the connection.
    * `on connection callback` : EPOLLIN(_READ) returned.
    * `on connection made callback`: when connection register to the ioloop.

    """

    def __init__(self, conn, address):
        self.conn = conn
        self.address = address

        self.events = None

        self.on_write_cb = None
        self.connection_made_cb = None
        self.on_connection_cb = None
        self.on_close_cb = None

    def read(self, bytes=1024, buffer=b''):
        try:
            while True:
                buffer += self.conn.recv(bytes)
        except socket.error:
            pass
        return buffer

    def write(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        try:
            self.conn.send(data)
        except socket.error:
            pass

    def close(self):
        # on close callback.
        if self.on_close_cb:
            try:
                self.on_close_cb()
            except NotImplementedError:
                pass
        # close connection
        self.conn.close()


class _Epoll(object):

    def __init__(self):
        self.epoller = select.epoll(flags=select.EPOLL_CLOEXEC)

    def register(self, fd, eventmask):
        self.epoller.register(fd, eventmask)

    def poll(self, timeout):
        return self.epoller.poll(timeout)

    def close(self):
        self.epoller.close()


class _Kqueue(object):

    MAX_EVENTS = 1024

    def __init__(self):
        self._kqueue = select.kqueue()

    def _control(self, fd, mode, flags):
        events = []
        if mode & IOLoop._READ:
            events.append(select.kevent(fd, select.KQ_FILTER_READ, flags))
        if mode & IOLoop._WRITE:
            events.append(select.kevent(fd, select.KQ_FILTER_WRITE, flags))
        for e in events:
            self._kqueue.control([e], 0)

    def register(self, fd, eventmask):
        self._control(fd, eventmask, select.KQ_EV_ADD | select.KQ_EV_CLEAR)

    def poll(self, timeout):
        if timeout < 0:
            timeout = None  # kqueue behaviour
        events = self._kqueue.control(None, self.MAX_EVENTS, timeout)
        results = defaultdict(lambda: IOLoop._NONE)
        for e in events:
            fd = e.ident
            if e.filter == select.KQ_FILTER_READ:
                if e.flags & select.KQ_EV_EOF:
                    results[fd] |= IOLoop._ERROR
                else:
                    results[fd] |= IOLoop._READ
            elif e.filter == select.KQ_FILTER_WRITE:
                if e.flags & select.KQ_EV_EOF:
                    results[fd] |= IOLoop._ERROR
                else:
                    results[fd] |= IOLoop._WRITE
        return results.items()

    def close(self):
        self._kqueue.close()


class IOLoop(object):

    # Global lock for creating global IOLoop instance
    _instance_lock = threading.Lock()

    # Constants from the epoll module
    _EPOLLIN = 0x001
    _EPOLLPRI = 0x002
    _EPOLLOUT = 0x004
    _EPOLLERR = 0x008
    _EPOLLHUP = 0x010
    _EPOLLRDHUP = 0x2000
    _EPOLLONESHOT = (1 << 30)
    _EPOLLET = (1 << 31)

    # Our events map exactly to the epoll events
    _NONE = 0
    _READ = _EPOLLIN
    _WRITE = _EPOLLOUT
    _ERROR = _EPOLLERR | _EPOLLHUP

    # Event dict for events string convertion.
    _EVENTS_DICT = {
        _EPOLLIN: "EPOLLIN",
        _EPOLLPRI: "EPOLLPRI",
        _EPOLLOUT: "EPOLLOUT",
        _EPOLLERR: "EPOLLERR",
        _EPOLLHUP: "EPOLLHUP",
        _EPOLLRDHUP: "EPOLLRDHUP",
        _EPOLLONESHOT: "EPOLLONESHOT",
        _EPOLLET: "EPOLLET",
        (_EPOLLHUP | _EPOLLOUT): "EPOLLOUT | EPOLLHUP",
        (_EPOLLIN | _EPOLLOUT): "EPOLLOUT | EPOLLIN",
        (_EPOLLIN | _EPOLLHUP | _EPOLLERR): "EPOLLIN | EPOLLHUP | EPOLLERR",
        (_EPOLLIN | _EPOLLOUT | _EPOLLERR | _EPOLLHUP):
        "EPOLLIN | EPOLLHUP | EPOLLERR | EPOLLOUT",
        # ...
    }

    @staticmethod
    def instance(num_backends):
        if not hasattr(IOLoop, "_instance"):
            with IOLoop._instance_lock:
                if not hasattr(IOLoop, "_instance"):
                    # New instance after double check
                    IOLoop._instance = IOLoop(num_backends)
        return IOLoop._instance

    def __init__(self, num_backends=-1):

        # single thread object
        self._impl = None
        if hasattr(select, 'epoll'):
            self._impl = _Epoll()
        elif hasattr(select, 'kqueue'):
            self._impl = _Kqueue()

        # acceptor
        self.acceptor = None

        # connections
        self.connections = {}

        # backends thread pool executor
        self.executor = ThreadPoolExecutor(max_workers=num_backends)

        # callbacks
        self.connection_made_cb = None
        self.on_write_cb = None
        self.on_connection_cb = None
        self.on_close_cb = None

        # logger
        self.logger = DefaultLogger()

    def start(self, timeout=1):
        while True:
            # epoll wait
            revents = self._impl.poll(timeout)
            if not revents:
                self.logger.debug("Nothing happened...")
            else:
                # process
                self._process_events(revents)

    def _process_events(self, revents):
        for fd, events in revents:
            self.logger.debug(
                "fd: %d, events: %s", fd, self.events_to_string(events))
            # active connection.
            connection = None
            try:
                connection = self.connections[fd]
            except KeyError:
                # Normally this will never happen.
                continue
            if events & self._READ:
                # silence mode for threadpool executor
                # if callbacks not available
                # or callbacks not working correctly
                # (with exception or programming error)
                # ioloop will will not do or notify anything.
                #
                #
                # connection.on_connection_cb(connection)
                self.executor.submit(
                    connection.on_connection_cb, connection)
            if events & self._WRITE:
                self.executor.submit(
                    connection.on_write_cb, connection)
            if events & self._ERROR:
                self.logger.error(
                    "fd: %d, events %s", fd, self.events_to_string(events))
                self.logger.error(
                    "fd: %d, connection closed.", fd)
                connection.close()
                del self.connections[fd]

    def bind(self, address):
        self.acceptor.bind(address)

    def register(self, fd, eventmask):
        self._impl.register(fd, eventmask)

    def register_acceptor(self, acceptor):
        self.acceptor = acceptor
        self.acceptor.ioloop = self
        self.connections[acceptor.fileno()] = acceptor.transport()
        # register
        self._impl.register(
            self.acceptor.fileno(), eventmask=IOLoop._READ | IOLoop._EPOLLET)

    def register_connector(self, connector):
        self.connections[connector.fileno()] = connector.transport
        self._impl.register(
            connector.fileno(), eventmask=connector.transport.events)
        connector.ioloop = self

    def events_to_string(self, events):
        try:
            return self._EVENTS_DICT[events]
        except KeyError:
            return "Unknown(%d)" % events

    def stop(self):
        self._impl.close()
        if self.acceptor:
            self.acceptor.close()
        for conn in self.connections:
            conn.close()
            # on close callback.
            # self.executor.submit(conn.on_close_cb)
        # clear
        self.connections.clear()

    def setloglevel(self, loglevel):
        # default logger level: DEBUG
        # see logging documentation for detail.
        self.logger.setlevel(loglevel)
