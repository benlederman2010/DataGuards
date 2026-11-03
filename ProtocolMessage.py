from ProtocolError import ProtocolError

class ProtocolMessage:
    """הודעה בפרוטוקול. בנויה משם פקודה ותוכן, ועוברת ברשת בצורה COMMAND|data."""

    SEPARATOR = "|"  # מפריד בין הפקודה לתוכן
    ENCODING = "utf-8"

    def __init__(self, command, data=""):
        """שומר את הפקודה באותיות גדולות. אם הפקודה ריקה או שיש בה מפריד, זורק ProtocolError."""
        command = command.upper()

        if command == "":
            raise ProtocolError("Command cannot be empty")

        if self.SEPARATOR in command:
            raise ProtocolError("Command cannot contain separator")

        self.__command = command
        self.__data = data

    @property
    def command(self):
        """שם הפקודה (קריאה בלבד)."""
        return self.__command

    @property
    def data(self):
        """תוכן ההודעה (קריאה בלבד)."""
        return self.__data

    def to_bytes(self) -> bytes:
        """מחזיר את ההודעה כבתים, בפורמט COMMAND|data ב-UTF-8."""
        text = self.__command + self.SEPARATOR + self.__data
        return text.encode(self.ENCODING)

    @classmethod
    def from_bytes(cls, raw):
        """בונה הודעה מבתים שהתקבלו. אם אין בהם מפריד, זורק ProtocolError."""
        text = raw.decode(cls.ENCODING)

        if cls.SEPARATOR not in text:
            raise ProtocolError("Invalid message format")

        # מפצלים רק במפריד הראשון, כדי שהתוכן עצמו יוכל להכיל |
        command, data = text.split(cls.SEPARATOR, 1)
        return cls(command, data)

    @classmethod
    def from_user_input(cls, line):
        """בונה הודעה מהשורה שהמשתמש הקליד. המילה הראשונה היא הפקודה והשאר הוא התוכן."""
        parts = line.split(" ", 1)

        if len(parts) == 1:
            command = parts[0]
            data = ""
        else:
            command = parts[0]
            data = parts[1]

        return cls(command, data)

    def __eq__(self, other) -> bool:
        """שתי הודעות שוות אם הפקודה והתוכן שלהן זהים."""
        if not isinstance(other, ProtocolMessage):
            return False
        return self.__command == other.command and self.__data == other.data

    def __repr__(self) -> str:
        """ייצוג מפורט, לשימוש בדיבוג."""
        return f"ProtocolMessage(command={self.__command!r}, data={self.__data!r})"

    def __str__(self) -> str:
        """ייצוג קריא להדפסה."""
        return f"[{self.__command}]{ProtocolMessage.SEPARATOR} {self.__data}"
