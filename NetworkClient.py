import socket


class NetworkClient:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 5000
        self.client_socket = socket.socket()
        self.client_socket.connect((self.host, self.port))

    def run(self):
        user_message = input("Enter your message: ")

        while user_message != "Exit":
            self.client_socket.send(user_message.encode())

            reply = self.client_socket.recv(1024)
            print(reply.decode())

            user_message = input("Enter your message: ")

        print("Client said bye")
        self.client_socket.close()