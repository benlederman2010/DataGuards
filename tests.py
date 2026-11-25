import threading
import time
import socket
import pytest
from datetime import datetime

from Protocol import Protocol
from ProtocolMessage import ProtocolMessage
from NetworkServer import NetworkServer

HOST = "127.0.0.1"
PORT = 8005


@pytest.fixture(scope="module", autouse=True)
def run_server():
    """פתיחת השרת ברקע לפני הרצת הבדיקות"""

    def server_thread_func():
        server = NetworkServer(host=HOST, port=PORT)
        server.start()

    thread = threading.Thread(target=server_thread_func, daemon=True)
    thread.start()
    time.sleep(0.2)  # המתנה קצרה לעליית השרת
    yield


def get_client_socket():
    """פונקציית עזר ליצירת חיבור לקוח"""
    sock = socket.socket()
    sock.connect((HOST, PORT))
    return sock


# --- בדיקה 1: PING ---
def test_ping():
    sock = get_client_socket()
    Protocol.send(sock, ProtocolMessage("PING"))
    response = Protocol.receive(sock)
    sock.close()

    assert response is not None
    assert response.command == "PING"
    assert response.data == "PONG"


# --- בדיקה 2: ECHO עם טקסט בעברית ---
def test_echo_hebrew():
    sock = get_client_socket()
    hebrew_text = "שלום עולם! בדיקה בעברית"
    Protocol.send(sock, ProtocolMessage("ECHO", hebrew_text))
    response = Protocol.receive(sock)
    sock.close()

    assert response is not None
    assert response.command == "ECHO"
    assert response.data == hebrew_text


# --- בדיקה 3: TIME ---
def test_time():
    sock = get_client_socket()
    Protocol.send(sock, ProtocolMessage("TIME"))
    response = Protocol.receive(sock)
    sock.close()

    assert response is not None
    assert response.command == "TIME"

    # וידוא שהזמן בפורמט תקין
    valid_time = True
    try:
        datetime.strptime(response.data, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        valid_time = False

    assert valid_time, "הזמן שהוחזר אינו בפורמט תקין"


# --- בדיקה 4: פקודה לא מוכרת ---
def test_unknown_command():
    sock = get_client_socket()
    Protocol.send(sock, ProtocolMessage("INVALID_CMD", "test"))
    response = Protocol.receive(sock)
    sock.close()

    assert response is not None
    assert response.command == "ERROR"


# --- בדיקה 5: EXIT ---
def test_exit():
    sock = get_client_socket()
    Protocol.send(sock, ProtocolMessage("EXIT"))
    response = Protocol.receive(sock)

    assert response is not None
    assert response.command == "BYE"

    # בדיקה שהחיבור אכן נסגר מהצד של השרת
    after_exit = Protocol.receive(sock)
    assert after_exit is None
    sock.close()


# --- בדיקה 6: חיבור כשהשרת כבוי ---
def test_connect_when_server_off():
    unused_port = 9999  # פורט שאין עליו שרת פעיל
    with pytest.raises(ConnectionRefusedError):
        sock = socket.socket()
        sock.connect((HOST, unused_port))
        sock.close()


# --- בדיקה 7: שתי בקשות רצופות ---
def test_consecutive_requests():
    sock = get_client_socket()

    # בקשה ראשונה
    Protocol.send(sock, ProtocolMessage("PING"))
    resp1 = Protocol.receive(sock)
    assert resp1.data == "PONG"

    # בקשה שנייה
    Protocol.send(sock, ProtocolMessage("ECHO", "test2"))
    resp2 = Protocol.receive(sock)
    assert resp2.data == "test2"

    sock.close()


# --- בדיקה 8: הודעה מפוצלת לפי מקטעי TCP ---
def test_chunked_tcp_message():
    sock = get_client_socket()
    msg = ProtocolMessage("ECHO", "SplitTCPPayloadData")
    msg_bytes = msg.to_bytes()

    length_bytes = len(msg_bytes).to_bytes(Protocol.HEADER_SIZE, Protocol.BYTE_ORDER)
    full_packet = length_bytes + msg_bytes

    # פיצול החבילה לשני חלקים ושליחתם בנפרד
    part1 = full_packet[:3]
    part2 = full_packet[3:]

    sock.sendall(part1)
    time.sleep(0.1)  # השהייה קצרה להפרדה ברשת
    sock.sendall(part2)

    response = Protocol.receive(sock)
    sock.close()

    assert response is not None
    assert response.command == "ECHO"
    assert response.data == "SplitTCPPayloadData"