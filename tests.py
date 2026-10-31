"""
מודול בדיקות יחידה (Unit Tests) עבור שרת ופרוטוקול התקשורת NetworkServer.
הבדיקות נכתבו באמצעות ספריית pytest ומכסות את מקרים 1-8 מטבלת הבדיקות.
"""

import threading
import time
import socket
import pytest
from datetime import datetime

from Protocol import Protocol
from ProtocolMessage import ProtocolMessage
from NetworkServer import NetworkServer

# הגדרות כתובת ופורט ייעודיים לבדיקות כדי למנוע התנגשויות
HOST = "127.0.0.1"
PORT = 8005


@pytest.fixture(scope="module", autouse=True)
def run_server():
    """
    Fixture של pytest שמפעיל את השרת ברקע (Thread נפרד) לפני תחילת הבדיקות.
    השרת פועל לאורך כל סדרת הבדיקות ונסגר אוטומטית עם סיומן (daemon thread).
    """

    def server_thread_func():
        server = NetworkServer(host=HOST, port=PORT)
        server.start()

    # יצירת והרצת תהליכון ברקע עבור השרת
    thread = threading.Thread(target=server_thread_func, daemon=True)
    thread.start()

    # השהייה קצרה (200 מילי-שניות) כדי לוודא שהשרת סיים לבצע bind ו-listen
    time.sleep(0.2)
    yield


def get_client_socket() -> socket.socket:
    """
    פונקציית עזר המייצרת סוקט לקוח חדש ומחברת אותו לשרת הבדיקות.

    :return: אובייקט socket מחובר לשרת
    """
    sock = socket.socket()
    sock.connect((HOST, PORT))
    return sock


# ==============================================================================
# בדיקה 1: PING
# ==============================================================================
def test_ping():
    """
    בדיקה #1: שליחת פקודת PING.
    תוצאה צפויה: קבלת תשובה PONG מהשרת.
    """
    # 1. התחברות לשרת
    sock = get_client_socket()

    # 2. שליחת הודעת PING
    Protocol.send(sock, ProtocolMessage("PING"))

    # 3. קבלת התשובה מהשרת
    response = Protocol.receive(sock)
    sock.close()

    # 4. אימות התשובה
    assert response is not None, "השרת לא החזיר תשובה"
    assert response.command == "PING", "פקודת התגובה אינה תואמת"
    assert response.data == "PONG", "גוף ההודעה אינו PONG"


# ==============================================================================
# בדיקה 2: ECHO עם טקסט בעברית
# ==============================================================================
def test_echo_hebrew():
    """
    בדיקה #2: שליחת פקודת ECHO עם תוכן בעברית.
    תוצאה צפויה: החזרת הטקסט בעברית במדויק (וידוא קידוד UTF-8 תקין).
    """
    sock = get_client_socket()
    hebrew_text = "שלום עולם! בדיקה בעברית"

    # שליחת הודעת ECHO עם מחרוזת עברית
    Protocol.send(sock, ProtocolMessage("ECHO", hebrew_text))
    response = Protocol.receive(sock)
    sock.close()

    # אימות שהטקסט שחזר זהה לחלוטין לקלט
    assert response is not None, "השרת לא החזיר תשובה"
    assert response.command == "ECHO"
    assert response.data == hebrew_text, "הטקסט בעברית שחזר אינו מדויק"


# ==============================================================================
# בדיקה 3: TIME
# ==============================================================================
def test_time():
    """
    בדיקה #3: שליחת פקודת TIME.
    תוצאה צפויה: קבלת שעה ותאריך תקפים מהשרת בפורמט YYYY-MM-DD HH:MM:SS.
    """
    sock = get_client_socket()
    Protocol.send(sock, ProtocolMessage("TIME"))
    response = Protocol.receive(sock)
    sock.close()

    assert response is not None, "השרת לא החזיר תשובה"
    assert response.command == "TIME"

    # וידוא שגוף ההודעה שמתקבל ניתן לפענוח כמבנה תאריך ושעה תקני
    valid_time = True
    try:
        datetime.strptime(response.data, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        valid_time = False

    assert valid_time, f"הזמן שהוחזר ('{response.data}') אינו בפורמט התקין %Y-%m-%d %H:%M:%S"


# ==============================================================================
# בדיקה 4: פקודה לא מוכרת
# ==============================================================================
def test_unknown_command():
    """
    בדיקה #4: שליחת פקודה שאינה מוגדרת בפרוטוקול.
    תוצאה צפויה: תגובת שגיאה (ERROR) מהשרת.
    """
    sock = get_client_socket()
    Protocol.send(sock, ProtocolMessage("INVALID_CMD", "test"))
    response = Protocol.receive(sock)
    sock.close()

    assert response is not None, "השרת לא החזיר תשובה"
    assert response.command == "ERROR", "השרת לא החזיר פקודת שגיאה ERROR"


# ==============================================================================
# בדיקה 5: EXIT
# ==============================================================================
def test_exit():
    """
    בדיקה #5: שליחת פקודת EXIT.
    תוצאה צפויה: קבלת תגובת BYE מהשרת וסגירה אלגנטית של החיבור מצידו.
    """
    sock = get_client_socket()
    Protocol.send(sock, ProtocolMessage("EXIT"))
    response = Protocol.receive(sock)

    # אימות קבלת תשובת ה-BYE מהשרת
    assert response is not None, "השרת לא החזיר תשובה לבקשת יציאה"
    assert response.command == "BYE"

    # וידוא שהחיבור אכן נסגר על ידי השרת (קריאה נוספת מחזירה None)
    after_exit = Protocol.receive(sock)
    assert after_exit is None, "החיבור לא נסגר מהצד של השרת לאחר פקודת EXIT"
    sock.close()


# ==============================================================================
# בדיקה 6: חיבור כשהשרת כבוי
# ==============================================================================
def test_connect_when_server_off():
    """
    בדיקה #6: ניסיון התחברות לפורט שאין בו שרת פעיל.
    תוצאה צפויה: תריסת חריגה ConnectionRefusedError וטיפול בה ללא קריסה.
    """
    unused_port = 9999  # פורט שאינו מאזין

    # אימות שמוקפצת שגיאת סירוב חיבור תקינה
    with pytest.raises(ConnectionRefusedError):
        sock = socket.socket()
        sock.connect((HOST, unused_port))
        sock.close()


# ==============================================================================
# בדיקה 7: שתי בקשות רצופות
# ==============================================================================
def test_consecutive_requests():
    """
    בדיקה #7: שליחת שתי בקשות שונות ברצף על גבי אותו חיבור סוקט פתוח.
    תוצאה צפויה: קבלת שתי תשובות תקינות ומתאימות בסדר הנכון.
    """
    sock = get_client_socket()

    # בקשה 1: PING
    Protocol.send(sock, ProtocolMessage("PING"))
    resp1 = Protocol.receive(sock)
    assert resp1 is not None
    assert resp1.data == "PONG"

    # בקשה 2: ECHO על אותו הסוקט
    Protocol.send(sock, ProtocolMessage("ECHO", "test2"))
    resp2 = Protocol.receive(sock)
    assert resp2 is not None
    assert resp2.data == "test2"

    sock.close()


# ==============================================================================
# בדיקה 8: הודעה מפוצלת לפי מקטעי TCP
# ==============================================================================
def test_chunked_tcp_message():
    """
    בדיקה #8: שליחת הודעה מפוצלת לשני מקטעי TCP נפרדים ברמת הרשת (Streaming).
    תוצאה צפויה: השרת יאגור את המדע עד לסיום הכותרת והאורך, ויפענח הודעה מלאה ותקינה.
    """
    sock = get_client_socket()
    msg = ProtocolMessage("ECHO", "SplitTCPPayloadData")
    msg_bytes = msg.to_bytes()

    # בניית החבילה הסטנדרטית (אורך בתים + תוכן)
    length_bytes = len(msg_bytes).to_bytes(Protocol.HEADER_SIZE, Protocol.BYTE_ORDER)
    full_packet = length_bytes + msg_bytes

    # פיצול פיזי של הבתים לשני חלקים שונים
    part1 = full_packet[:3]
    part2 = full_packet[3:]

    # שליחת החלק הראשון
    sock.sendall(part1)
    time.sleep(0.1)  # השהייה קצרה ליצירת הפרדה בין המקטעים ברשת

    # שליחת החלק השני
    sock.sendall(part2)

    # קבלת התשובה והנחה שהשרת חיכה לכל הבתים
    response = Protocol.receive(sock)
    sock.close()

    assert response is not None, "השרת לא נתן מענה להודעה מפוצלת"
    assert response.command == "ECHO"
    assert response.data == "SplitTCPPayloadData", "פענוח גוף ההודעה המפוצלת נכשל"