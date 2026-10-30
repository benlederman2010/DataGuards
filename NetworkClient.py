"""
מודול הלקוח (Client) עבור התקשורת מול השרת.
המודול מנהל את החיבור, קולט פקודות מהמשתמש, ושולח אותן על בסיס חוקי הפרוטוקול.
"""

import socket
from Protocol import Protocol
from ProtocolMessage import ProtocolMessage


class NetworkClient:
    """
    מחלקה המייצגת לקוח רשת מבוסס פרוטוקול TCP מותאם אישית.
    המחלקה עוטפת את ניהול הסוקט, בניית ההודעות ופיענוח התשובות מהשרת.
    """

    def __init__(self):
        """
        פעולה בונה (Constructor).
        מאתחלת את כתובת השרת, יוצרת סוקט מסוג TCP, ויוצרת את החיבור ההתחלתי.
        """
        self.host = "127.0.0.1"  # כתובת ה-IP של השרת (Localhost)
        self.port = 8000  # הפורט שעליו השרת מאזין
        self.client_socket = socket.socket()

        # יצירת חיבור ישיר לשרת בעת יצירת האובייקט
        try:
            self.client_socket.connect((self.host, self.port))
        except Exception as e:
            print(f"Error: Could not connect to server at {self.host}:{self.port}.")
            print("Make sure the server is running and try again.")

    def run(self):
        """
        הלולאה המרכזית של הלקוח.
        הפעולה קולטת קלט מהמשתמש, ממירה אותו לאובייקט הודעה תקני, שולחת לשרת,
        ומדפיסה את התשובה המתקבלת. התהליך חוזר על עצמו עד להקלדת "Exit".
        """
        # קבלת קלט ראשוני מהמשתמש
        user_message = input("Enter your message: ")

        # המשך תקשורת כל עוד המשתמש לא ביקש לצאת
        while user_message != "Exit":
            # 1. המרת הטקסט הגולמי לאובייקט ProtocolMessage תקני
            user_message = ProtocolMessage.from_user_input(user_message)

            # 2. שליחת הודעת הפרוטוקול דרך הסוקט לשרת
            Protocol.send(self.client_socket, user_message)

            # 3. המתנה לתשובה מהשרת וקבלתה כאובייקט ProtocolMessage
            reply = Protocol.receive(self.client_socket)

            # 4. וידוא שהתשובה תקינה (לא שגיאה או ניתוק) והדפסתה
            if reply is not None:
                print(reply)

            # קבלת קלט חדש עבור האיטרציה הבאה
            user_message = input("Enter your message: ")

        # יציאה מסודרת מהלולאה וסגירת הסוקט
        print("Client said bye")
        self.client_socket.close()


# נקודת ההתחלה של התוכנית
if __name__ == "__main__":
    client = NetworkClient()
    client.run()