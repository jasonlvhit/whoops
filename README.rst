Whoops.
=======

Whoops, lightweight, asynchronous, event-driven network programming snippets(maybe framework) in Python.

Requirements
------------

- Python 3.0 +
- Linux 2.5 + with epoll, or BSD/Mac OS X with kqueue

Usage
-----
Here is a simple echo server and echo client example. ::


    from whoops import ioloop, async_server

    class EchoServer(async_server.AsyncServer):

        def on_connection(self, conn):
            data = conn.read()
            print(data)
            conn.write(data)

    if __name__ == "__main__":
        EchoServer(ioloop.IOLoop.instance(num_backends=1000), 
        ('127.0.0.1', 8888)).listen()

async echo client::


    from whoops import ioloop, async_client

    class EchoClient(async_client.AsyncClient):

        def on_write(self, conn):
            conn.write("hello")

        def on_connection(self, conn):
            print(conn.read())

    if __name__ == "__main__":
        ioloop = ioloop.IOLoop.instance(num_backends=1000)
        client = EchoClient(ioloop, ('127.0.0.1', 8888))
        ioloop.start()
        client.connect()  


See `examples <https://github.com/jasonlvhit/whoops/tree/master/examples>`__ for more examples.


License
----------

The MIT License (MIT)

Copyright (c) 2015 jasonlvhit

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
