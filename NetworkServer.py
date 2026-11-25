import socket
import threading
from ClientHandler import ClientHandler


class NetworkServer:
    def __init__(self, host="127.0.0.1", port=8000):
        self.__host = host
        self.__port = port
        self.__server_socket = None
        self.__clients = []
        self.__lock = threading.Lock()
        self.__running = False

    def start(self):
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__server_socket.bind((self.__host, self.__port))
        self.__server_socket.listen()
        self.__running = True
        print(f"SERVER Listening on {self.__host}:{self.__port}...")

        try:
            while self.__running:
                try:
                    client_socket, client_address = self.__server_socket.accept()
                except OSError:
                    break

                print(f"SERVER Client connected from {client_address}")
                handler = ClientHandler(client_socket, client_address, self)
                with self.__lock:
                    self.__clients.append(handler)
                handler.start()
        finally:
            self.stop()

    def remove_client(self, handler):
        with self.__lock:
            if handler in self.__clients:
                self.__clients.remove(handler)

    def client_count(self) -> int:
        with self.__lock:
            return len(self.__clients)

    def stop(self):
        self.__running = False
        with self.__lock:
            active_clients = list(self.__clients)
            self.__clients.clear()

        for handler in active_clients:
            handler.stop()

        if self.__server_socket:
            try:
                self.__server_socket.close()
            except OSError:
                pass
            self.__server_socket = None
        print("SERVER stopped.")


if __name__ == "__main__":
    server = NetworkServer(host = "127.0.0.1", port=8000)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()