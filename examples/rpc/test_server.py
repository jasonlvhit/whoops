from whoops import ioloop
from jsonrpc import JSONRPCServer

class MyServer(JSONRPCServer):
    @JSONRPCServer.jsonrpc_method
    def subtract(self, a, b):
        return a - b

    def foobar(self):
        pass
    
    
if __name__ == '__main__':
    MyServer(ioloop.IOLoop.instance(num_backends=1000),
               ('127.0.0.1', 8888)).listen()
