# Simple JSON RPC server and client implementation base on
# Whoops async server and client using TCP protocol.
#
# JSON-RPC protocaol version 2.0
# author: jasonlvhit
# LICENCE: MIT LICENSE Copyright 2015 jasonlvhit

# Examples:

# In these examples, --> denotes data sent to a service (request),
# while <-- denotes data coming from a service.
# (Although <-- often is called response in client–server computing,
# depending on the JSON-RPC version it does not necessarily imply answer
# to a request).

# Procedure call with positional parameters:
#
# --> {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}
# <-- {"jsonrpc": "2.0", "result": 19, "id": 1}
# --> {"jsonrpc": "2.0", "method": "subtract", "params": [23, 42], "id": 2}
# <-- {"jsonrpc": "2.0", "result": -19, "id": 2}
# Procedure call with named parameters:

# --> {"jsonrpc": "2.0", "method": "subtract", "params": {"a": 23, "b": 42}, "id": 3}
# <-- {"jsonrpc": "2.0", "result": 19, "id": 3}
# --> {"jsonrpc": "2.0", "method": "subtract", "params": {"minuend": 42, "subtrahend": 23}, "id": 4}
# <-- {"jsonrpc": "2.0", "result": 19, "id": 4}
# Notification:

# --> {"jsonrpc": "2.0", "method": "update", "params": [1,2,3,4,5]}
# --> {"jsonrpc": "2.0", "method": "foobar"}
# Procedure call of non-existent procedure:

# --> {"jsonrpc": "2.0", "method": "foobar", "id": 10}
# <-- {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Procedure not found."}, "id": 10}
# Procedure call with invalid JSON:

# --> {"jsonrpc": "2.0", "method": "foobar", "params": "bar", "baz"}
# <-- {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": null}
# Procedure call with invalid JSON-RPC:

# --> [1,2,3]
# <-- [
#   {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": null},
#   {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": null},
#   {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": null}
# ]
# --> {"jsonrpc": "2.0", "method": 1, "params": "bar"}
# <-- {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": null}

import json

from . import ioloop
from . import async_server
from . import async_client

JSONRPC_CODES = {
    -32600: "Invalid Request.",
    -32601: "JSON-RPC Version Not Supported.",
    -32603: "Parse error."
}


class JSONRPCServer(async_server.AsyncServer):

    version = "2.0"

    base_error = {
        "code": -1,
        "message": "null"
    }

    def on_connection(self, conn):
        data = conn.read()
        print(data)
        jsonobj = None
        result = {
            "jsonrpc": self.version,
            "error": None,
            "id": None,
            # result
        }

        try:
            jsonobj = json.loads(data)
        except ValueError as e:
            result['error'] = self.process_error(-32600)
            conn.write(json.dumps(result))
            conn.write('\n')
            return

        if isinstance(jsonobj, list):
            for obj in jsonobj:
                conn.write(json.dumps(self.process_single_request(obj)))
                conn.write('\n')
            return

        if isinstance(jsonobj, dict):
            conn.write(json.dumps(self.process_single_request(jsonobj)))
            conn.write('\n')
            return

        result['error'] = self.process_error(-32600)
        conn.write(json.dumps(result))
        conn.write('\n')

    def process_error(self, error_code=-1):
        error = self.base_error
        error['code'] = error_code
        error['message'] = JSONRPC_CODES[error_code]
        return error

    def process_single_request(self, jsonobj):
        result = {
            "jsonrpc": self.version,
            "error": None,
            "id": None,
            # result
        }

        # request data should be a python dict.
        if not isinstance(jsonobj, dict):
            result['error'] = self.process_error(-32600)
            return result

        # request id
        try:
            result['id'] = jsonobj['id']
        except KeyError as e:
            result['error'] = self.process_error(-32600)
            return result

        # request version: jsonrpc: 2.0
        request_version = None
        try:
            request_version = jsonobj['jsonrpc']
        except KeyError as e:
            result['error'] = self.process_error(-32600)
            return result
        if request_version != '2.0':
            result['error'] = self.process_error(-32601)
            return result

        # method
        method = None
        try:
            method = jsonobj['method']
        except KeyError as e:
            result['error'] = self.process_error(-32600)
            return result

        # params
        params = None
        try:
            params = jsonobj['params']
        except KeyError as e:
            pass

        if params:
            if not (isinstance(params, list) or isinstance(params, dict)):
                result['message'] = "Parse error."
                return result

        re = self.process_method(method, params)
        if re and not isinstance(re, Exception):
            result['result'] = re
        return result

    def process_method(self, method, params):
        try:
            if not params:
                return getattr(self, method)()
            if isinstance(params, list):
                return getattr(self, method)(*params)
            if isinstance(params, dict):
                return getattr(self, method)(**params)
        except Exception as e:
            return e

    def subtract(self, a, b):
        return a - b

    def foobar(self):
        pass


class JSONRPCClient(async_client.AsyncClient):
    pass
