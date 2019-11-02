from jsonrpc import JSONRPCClient

if __name__ == "__main__":
    s = JSONRPCClient(("127.0.0.1", 8888))
    r = s.subtract(42, 19)
    print(r)
