import socket
import Protocol
import ProtocolMessage

class NetworkClient:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 5000
        self.client_socket = socket.socket()
        self.client_socket.connect((self.host, self.port))

    def run(self):
        user_message = input("Enter your message: ")

        while user_message != "Exit":
            user_message = ProtocolMessage.from_user_input(user_message)

            Protocol.send(self.client_socket, user_message)

            reply = Protocol.receive(self.client_socket)
            if reply is not None:
                print(reply)

            user_message = input("Enter your message: ")

        print("Client said bye")
        self.client_socket.close()