"""השרת: מקבל לקוח, קורא ממנו פקודות לפי הפרוטוקול ועונה להן."""

import socket
from datetime import datetime
from Protocol import Protocol
from ProtocolError import ProtocolError
from ProtocolMessage import ProtocolMessage

class NetworkServer:
    """שרת TCP שעונה לפקודות PING, ECHO, TIME ו-EXIT. בשלב הזה הוא מטפל בלקוח אחד."""

    def __init__(self,host = "127.0.0.1",port = 8000):
        """שומר את הכתובת והפורט. הסוקט עצמו נוצר רק ב-start."""
        self.__host = host
        self.__port = port
        self.__server_socket = None

    def start(self):
        """פותח סוקט, מאזין לחיבורים ומעביר את הלקוח שהתחבר לטיפול."""

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
        """
        מטפל בלקוח אחד: קורא בקשה, שולח תשובה וחוזר על זה עד שמגיעה הפקודה EXIT.
        אם ההודעה לא בפורמט הפרוטוקול, שולח ללקוח ERROR. בסוף סוגר את הסוקט של הלקוח.
        """
        try:
            while True:
                msg = Protocol.receive(client_socket)
                print(f"Received from {client_address}: {msg}")

                response = self.__process(msg)
                Protocol.send(client_socket, response)

                if msg.command == "EXIT":
                    print(f"Client {client_address} requested exit.")
                    break

        except ProtocolError as e:
            error_msg = ProtocolMessage("ERROR", f"Protocol error: {e}")
            Protocol.send(client_socket, error_msg)
        finally:
            client_socket.close()
            print("Server shutdown.")

    @staticmethod
    def __process(msg: ProtocolMessage) -> ProtocolMessage:
        """מקבל בקשה ומחזיר את התשובה שלה. פקודה לא מוכרת מקבלת ERROR."""
        command = msg.command
        if command == "PING":
            return ProtocolMessage("PING","PONG")
        elif command == "ECHO":
            return ProtocolMessage("ECHO", msg.data)
        elif command == "TIME":
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return ProtocolMessage("TIME", current_time)
        elif command == "EXIT":
            return ProtocolMessage("BYE", "Connection closed")
        else:
            return ProtocolMessage("ERROR", f"Unknown command '{command}'")

if __name__ == "__main__":
    server = NetworkServer(host="127.0.0.1", port=8000)
    server.start()
