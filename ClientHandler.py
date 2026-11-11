import threading
import socket
from Protocol import Protocol
from ProtocolMessage import ProtocolMessage
from ProtocolError import ProtocolError
from datetime import datetime


class ClientHandler(threading.Thread):
    def __init__(self,client_socket,client_address,server):
        super().__init__()
        self.__sock = client_socket
        self.__address = client_socket
        self.__server = server
        self.__name = f"Client - {client_address[0]} : {client_address[1]} "

    def run(self):
        try:
            self.__serve()
        finally:
            self.__server.remove_client(self)
            self.__sock.close()
            print(f"[-] {self.name} disconnected.")

    def __serve(self):

        while True:
            try:
                msg = Protocol.recive(self.__sock,self.__address)
                if not msg:
                    break

                print(f"Received from {self.__address}: {msg}")
                response = self.__process(msg)

                if not self.__reply(response) or response.command == "BYE":
                    break
            except ProtocolError as e:
                self.__reply(ProtocolMessage("ERROR", str(e)))

    def __process(self,msg):
        command = msg.command
        if command == "PING":
            return ProtocolMessage("PONG")
        elif command == "ECHO":
            return ProtocolMessage("ECHO", msg.data)
        elif command == "TIME":
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return ProtocolMessage("TIME", current_time)
        elif command == "EXIT":
            return ProtocolMessage("BYE", "Connection closed")
        elif command == "CLIENTS":
            return ProtocolMessage("CLIENTS", str(self.__server.client_count()))
        else:
            return ProtocolMessage("ERROR", f"Unknown command '{command}'")

    def __reply(self, message):
        try:
            Protocol.send(self.__sock, message)
            return True
        except Exception:
            return False

    def stop(self):
        try:
            self.__sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass