import threading
import socket
from Protocol import Protocol
from ProtocolMessage import ProtocolMessage
from ProtocolError import ProtocolError


class NetworkClient:
    CONNECT_TIMEOUT: int = 5
    REPLY_TIMEOUT: int = 10

    def __init__(self, ip="127.0.0.1", port=8000):
        self.__address = (ip, port)
        self.__lock = threading.Lock()
        self.__connected = False
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.__sock.settimeout(self.CONNECT_TIMEOUT)
        self.__sock.connect(self.__address)
        self.__connected = True

    @property
    def connected(self) -> bool:
        return self.__connected

    def request(self, message: ProtocolMessage) -> ProtocolMessage:
        with self.__lock:
            if not self.connected:
                raise ConnectionError("Client is not connected to the server.")

            try:
                self.__sock.settimeout(self.REPLY_TIMEOUT)
                Protocol.send(self.__sock, message)
                reply = Protocol.receive(self.__sock)

                if reply is None:
                    self.__connected = False
                    raise ConnectionError("Server closed the connection.")

                return reply

            except (socket.timeout, socket.error, OSError) as e:
                self.__connected = False
                raise ConnectionError(f"Communication error: {e}") from e

    def close(self):
        with self.__lock:
            self.__connected = False
            try:
                self.__sock.close()
            except (socket.error, OSError):
                pass

    @staticmethod
    def print_instructions():
        print("=" * 55)
        print("Welcome to DataGuards Client! Available commands:")
        print("  PING           - Check connection with the server (returns PONG)")
        print("  ECHO <text>    - Echo back the given text (e.g., ECHO Hello)")
        print("  TIME           - Get the current date and time from the server")
        print("  CLIENTS        - Get the number of connected clients")
        print("  EXIT           - Close the connection and exit the client")
        print("=" * 55)

    def run(self):
        self.print_instructions()

        try:
            while self.__connected:
                raw_input = input("Enter your command: ").strip()
                if not raw_input:
                    continue

                try:
                    msg = ProtocolMessage.from_user_input(raw_input)
                except ProtocolError as e:
                    print(f"Invalid input: {e}")
                    continue

                reply = self.request(msg)
                if reply is not None:
                    print(reply)

                if msg.command == "EXIT":
                    break

        except (ConnectionError, KeyboardInterrupt) as e:
            if isinstance(e, ConnectionError):
                print(f"Connection lost: {e}")
            else:
                try:
                    if self.__connected:
                        self.request(ProtocolMessage("EXIT"))
                except ConnectionError:
                    pass
        finally:
            print("Client disconnected cleanly.")
            self.close()


if __name__ == "__main__":
    client = NetworkClient()
    client.run()