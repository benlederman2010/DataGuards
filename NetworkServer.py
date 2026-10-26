import socket


class NetworkServer:
    def __init__(self,host,port):
        self.__host = host
        self.__port = port
        self.__server_socket = None

    def start(self):

        self.__server_socket = socket.socket()
        self.__server_socket.bind((self.__host, self.__port))
        self.__server_socket.listen(1)
        print(f"SERVER Listening on {self.__host}:{self.__port}...")

        while True:
            client_socket, client_address = self.__server_socket.accept()
            print(f"SERVER Client connected from {client_address}")
            self.__handle_client(client_socket)
            self.__server_socket.close()

    def __handle_client(self,client_socket):
        pass

    def __process(self):
        pass