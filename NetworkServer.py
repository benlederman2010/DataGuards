import socket
from threading import Lock
from ClientHandler import ClientHandler


class NetworkServer:
    def __init__(self, ip="127.0.0.1", port=8000):
        self.__ip = ip
        self.__port = port
        self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__handlers: list[ClientHandler] = []
        self.__lock = Lock()
        self.__running = False

    def start(self):
        self.__server.bind((self.__ip, self.__port))
        self.__server.listen(5)
        self.__running = True
        print(f"SERVER Listening on {self.__ip}:{self.__port}...")

        try:
            while self.__running:
                try:
                    client_socket, client_address = self.__server.accept()
                except OSError:
                    break

                print(f"SERVER Client connected from {client_address}")
                handler = ClientHandler(client_socket, client_address, self)
                with self.__lock:
                    self.__handlers.append(handler)
                handler.start()
        except KeyboardInterrupt:
            print("\nSERVER Stopping...")
        finally:
            self.__shutdown()

    def remove_handler(self, handler: ClientHandler):
        with self.__lock:
            if handler in self.__handlers:
                self.__handlers.remove(handler)

    def client_count(self) -> int:
        with self.__lock:
            return len(self.__handlers)

    def __shutdown(self):
        self.__running = False
        try:
            self.__server.close()
        except OSError:
            pass

        with self.__lock:
            handlers_copy = list(self.__handlers)

        for handler in handlers_copy:
            handler.stop()

        for handler in handlers_copy:
            handler.join(timeout=1.0)

        with self.__lock:
            self.__handlers.clear()
        print("SERVER Shutdown complete.")


if __name__ == "__main__":
    server = NetworkServer(ip="127.0.0.1", port=8000)
    server.start()