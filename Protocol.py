import socket
from typing import Literal
from ProtocolMessage import ProtocolMessage
from ProtocolError import ProtocolError


class Protocol:
    HEADER_SIZE: int = 4
    BYTE_ORDER: Literal["little", "big"] = "big"
    MAX_LENGTH: int = 2 ** 32 - 1
    COMMANDS: list[str] = ["TIME", "ECHO", "PING", "EXIT", "CLIENTS"]
    COMMANDS_WITH_DATA: list[str] = ["ECHO"]

    @staticmethod
    def send(sock: socket.socket, message: ProtocolMessage) -> None:
        msg_bytes = message.to_bytes()
        msg_length = len(msg_bytes)

        if msg_length > Protocol.MAX_LENGTH:
            raise ProtocolError("Message is too long")

        length_bytes = msg_length.to_bytes(Protocol.HEADER_SIZE, Protocol.BYTE_ORDER)
        sock.sendall(length_bytes + msg_bytes)

    @staticmethod
    def receive(sock: socket.socket) -> ProtocolMessage:
        # קריאת כותרת האורך
        length_bytes = Protocol.__recv_exact(sock, Protocol.HEADER_SIZE)
        if not length_bytes:
            return None

        msg_length = int.from_bytes(length_bytes, Protocol.BYTE_ORDER)

        msg_bytes = Protocol._recv_exact(sock, msg_length)
        if not msg_bytes:
            return None

        return ProtocolMessage.from_bytes(msg_bytes)

    @staticmethod
    def _recv_exact(sock: socket.socket, n: int) -> bytes | None:
        data = bytearray()
        while len(data) < n:
            try:
                packet = sock.recv(n - len(data))
                if not packet:
                    return None
                data.extend(packet)
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                return None
        return bytes(data)