import socket

remote = ("127.0.0.1", 8888)


def main():
    connect_socket = socket.socket(socket.AF_INET)
    connect_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connect_socket.connect(remote)

    while True:
        user_input = input("Input:")
        data = user_input.encode("utf-8")

        connect_socket.send(data)

        t = connect_socket.recv(1024)
        print(t)


if __name__ == "__main__":
    main()
