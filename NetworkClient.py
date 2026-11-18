"""
מודול הלקוח (Client) עבור התקשורת מול השרת.
המודול מנהל את החיבור, קולט פקודות מהמשתמש, ושולח אותן על בסיס חוקי הפרוטוקול.
"""

import threading
from threading import Lock
import socket
import Protocol
import ProtocolMessage


class NetworkClient:
    """
    מחלקה המייצגת לקוח רשת מבוסס פרוטוקול TCP מותאם אישית.
    המחלקה עוטפת את ניהול הסוקט, בניית ההודעות ופיענוח התשובות מהשרת.
    """
    CONNECT_TIMEOUT: int = 5
    REPLY_TIMEOUT: int = 10


    def __init__(self, ip = "127.0.0.1", port = 8000):
        """
        פעולה בונה (Constructor).
        מאתחלת את כתובת השרת, יוצרת סוקט מסוג TCP, ויוצרת את החיבור ההתחלתי.
        """
        self.__address = (ip,port)
        self.__lock = threading.Lock()
        self.__connected = False
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.__sock.settimeout(self.CONNECT_TIMEOUT)
        # יצירת חיבור ישיר לשרת בעת יצירת האובייקט
        self.__sock.connect(self.__address)
        self.__connected = True

    @property
    def connected(self) -> bool:
        """
             מחזירה את מצב החיבור הנוכחי של הלקוח לשרת (לקריאה בלבד).
        """
        return self.__connected

    def request(self, message: ProtocolMessage) -> ProtocolMessage:
        """
            שולחת הודעת פרוטוקול לשרת ומחזירה את תשובתו תחת מנעול.
            מטפלת במצבי ניתוק ו-timeout.
        """
        with self.__lock:

            if not self.connected:
                raise ConnectionError("Client is not connected to the server.")

            try:
                # הגדרת זמן ההמתנה המרבי לקבלת תשובה מהשרת
                self.__sock.settimeout(self.REPLY_TIMEOUT)

                # שליחת ההודעה לשרת על פי חוקי הפרוטוקול
                Protocol.send(self.__sock, message)

                # המתנה וקבלת התשובה מהשרת כאובייקט ProtocolMessage
                reply = Protocol.receive(self.__sock)

                # בדיקה שהתשובה תקינה (None מעיד שהשרת סגר את החיבור)
                if reply is None:
                    self.__connected = False
                    raise ConnectionError("Server closed the connection.")

                return reply

            except (socket.timeout, socket.error, OSError) as e:
                # במקרה של תקלת תקשורת או חריגה מזמן ההמתנה - סימון החיבור כמנותק
                self.__connected = False
                raise ConnectionError(f"Communication error: {e}") from e
    def close(self):
        """
            סוגרת את הסוקט בצורה בטוחה ומעדכנת את מצב החיבור למנותק (False).
            הפעולה מתבצעת תחת מנעול כדי למנוע סגירה בזמן שליחה או קבלה.
        """
        with self.__lock:
            self.__connected = False

            try:
                self.__sock.close()
            except (socket.error, OSError):
                pass

    def run(self):
        """
        הלולאה המרכזית של הלקוח.
        הפעולה קולטת קלט מהמשתמש, ממירה אותו לאובייקט הודעה תקני, שולחת לשרת,
        ומדפיסה את התשובה המתקבלת. התהליך חוזר על עצמו עד להקלדת "Exit".
        """
        # קבלת קלט ראשוני מהמשתמש
        try:
            user_message = input("Enter your message: ")

            # המשך תקשורת כל עוד המשתמש לא ביקש לצאת
            while user_message != "Exit" and self.__connected:
                # 1. המרת הטקסט הגולמי לאובייקט ProtocolMessage תקני
                user_message = ProtocolMessage.from_user_input(user_message)

                # 2. שליחת הודעת הפרוטוקול דרך הסוקט לשרת
                reply = self.request(user_message)

                # 4. וידוא שהתשובה תקינה (לא שגיאה או ניתוק) והדפסתה
                if reply is not None:
                    print(reply)

                # קבלת קלט חדש עבור האיטרציה הבאה
                user_message = input("Enter your message: ")

        except ConnectionError as e:
            print(f"Connection lost: {e}")

        # יציאה מסודרת מהלולאה וסגירת הסוקט
        print("Client said bye")
        self.close()


# נקודת ההתחלה של התוכנית
if __name__ == "__main__":
    client = NetworkClient()
    client.run()