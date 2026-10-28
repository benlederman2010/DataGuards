import socket
from datetime import datetime
import Protocol
import ProtocolError
import ProtocolMessage

class NetworkServer:
    def __init__(self,host = "127.0.0.1",port = 8000):
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
            self.__handle_client(client_socket,client_address)
            self.__server_socket.close()

    def __handle_client(self,client_socket,client_address):
        try:
            while True:
                msg = Protocol.recive(client_socket,client_address)
                print(f"Received from {client_address}: {msg}")

                response = self.__process(msg)
                Protocol.send(client_socket, response)

                if msg.command == "EXIT":
                    print(f"Client {client_address} requested exit.")
                    break

        except ProtocolError as e:
            error_msg = ProtocolMessage("ERROR", f"Protocol error: {e}")
            Protocol.send(client_socket, error_msg)








    def __process(self):
        pass