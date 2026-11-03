"""
שלב ד - בדיקות חובה (pytest)
כל בדיקה מתאימה לשורה בטבלת ההוראות.
"""

import socket
import threading
import time
from datetime import datetime

import pytest

import NetworkClient as network_client_module
from NetworkServer import NetworkServer
from Protocol import Protocol
from ProtocolMessage import ProtocolMessage

HOST = "127.0.0.1"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind((HOST, 0))
        return s.getsockname()[1]


def _connect(port: int, retries: int = 50) -> socket.socket:
    for _ in range(retries):
        try:
            sock = socket.socket()
            sock.settimeout(3)
            sock.connect((HOST, port))
            return sock
        except ConnectionRefusedError:
            sock.close()
            time.sleep(0.05)
    raise RuntimeError("server did not start")


@pytest.fixture
def client():
    """מפעיל שרת ב-thread נפרד ומחזיר סוקט מחובר אליו."""
    port = _free_port()
    server = NetworkServer(HOST, port)
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    sock = _connect(port)
    yield sock
    sock.close()


def _ask(sock, text):
    Protocol.send(sock, ProtocolMessage.from_user_input(text))
    return Protocol.receive(sock)


# 1. PING -> PONG
def test_ping_returns_pong(client):
    reply = _ask(client, "PING")
    assert reply.command == "PING"
    assert reply.data == "PONG"


# 2. ECHO עם טקסט בעברית -> החזרת הטקסט במדויק
def test_echo_hebrew_text_returned_exactly(client):
    text = "שלום עולם! בדיקה 123"
    reply = _ask(client, f"ECHO {text}")
    assert reply.command == "ECHO"
    assert reply.data == text


# 3. TIME -> שעה תקפה מהשרת
def test_time_returns_valid_server_time(client):
    reply = _ask(client, "TIME")
    assert reply.command == "TIME"
    server_time = datetime.strptime(reply.data, "%Y-%m-%d %H:%M:%S")
    assert abs((datetime.now() - server_time).total_seconds()) < 5


# 4. פקודה לא מוכרת -> תגובת שגיאה
def test_unknown_command_returns_error(client):
    reply = _ask(client, "BLABLA something")
    assert reply.command == "ERROR"
    assert "BLABLA" in reply.data


# 5. EXIT -> תגובה וסגירת חיבור
def test_exit_replies_and_closes_connection(client):
    reply = _ask(client, "EXIT")
    assert reply.command == "BYE"
    # השרת סגר את החיבור: קריאה נוספת מחזירה None
    assert Protocol.receive(client) is None


# 6. חיבור כשהשרת כבוי -> טיפול בשגיאה ללא קריסה לא מבוקרת
def test_connect_when_server_down_handled_gracefully(monkeypatch, capsys):
    class RefusingSocket:
        def connect(self, addr):
            raise ConnectionRefusedError()

        def close(self):
            pass

    monkeypatch.setattr(network_client_module.socket, "socket", RefusingSocket)

    # הלקוח מדפיס הודעה ויוצא מסודר (exit) - לא חריגה גולמית
    with pytest.raises(SystemExit):
        network_client_module.NetworkClient()
    assert "Could not connect" in capsys.readouterr().out


# 7. שתי בקשות רצופות -> שתי תשובות תקינות
def test_two_consecutive_requests(client):
    first = _ask(client, "PING")
    second = _ask(client, "ECHO hello")
    assert (first.command, first.data) == ("PING", "PONG")
    assert (second.command, second.data) == ("ECHO", "hello")


# 8. הודעה מפוצלת למקטעי TCP -> פענוח הודעה אחת מלאה
def test_message_split_into_tcp_segments(client):
    msg = ProtocolMessage("ECHO", "הודעה מפוצלת")
    body = msg.to_bytes()
    raw = len(body).to_bytes(Protocol.HEADER_SIZE, Protocol.BYTE_ORDER) + body

    # פיצול לבתים בודדים, כולל באמצע הכותרת ובאמצע תו בעברית (UTF-8)
    for i in range(len(raw)):
        client.sendall(raw[i:i + 1])
        time.sleep(0.01)

    reply = Protocol.receive(client)
    assert reply.command == "ECHO"
    assert reply.data == "הודעה מפוצלת"