import socket
import threading
from ClientHandler import ClientHandler

class NetworkServer:
    def __init__(self, host="127.0.0.1", port=8000):
        self.__host = host
        self.__port = port
        self.__server = None
        self.__handlers = []
        self.__lock = threading.Lock()
        self.__running = False

    def start(self):
        self.__server = socket.socket()
        self.__server.bind((self.__host,self.__port))
        self.__server.listen()
        self.__running = True
        print(f"[+] Server listening...")
        while self.__running:
            client_sock, addr = self.__server.accept()
            print(f"[+] New connection from {addr}")
            handler = ClientHandler(client_sock, addr, self)
            with self.__lock:
                self.__handlers.append(handler)
            handler.start()


    def remove_handler(self, handler):
        with self.__lock:
            if handler in self.__handlers:
                self.__handlers.remove(handler)

    def client_count(self) :
        with self.__lock:
            return len(self.__handlers)

    def shutdown(self):
        self.__running = False
        self.__server.close()

        with self.__lock:
            handlers_copy = list(self.__handlers)

        for handler in handlers_copy:
            handler.stop()

        for handler in handlers_copy:
            handler.join()

if __name__ == "__main__":
    server = NetworkServer(host="127.0.0.1", port=8000)
    server.start()
