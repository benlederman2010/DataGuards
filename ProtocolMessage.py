from ProtocolError import ProtocolError

class ProtocolMessage:
    SEPARATOR = "|"
    ENCODING = "utf-8"

    def __init__(self, command, data=""):
        command = command.upper()

        if command == "":
            raise ProtocolError("Command cannot be empty")

        if self.SEPARATOR in command:
            raise ProtocolError("Command cannot contain separator")

        self.__command = command
        self.__data = data

    @property
    def command(self):
        return self.__command

    @property
    def data(self):
        return self.__data

    def to_bytes(self) -> bytes:
        text = self.__command + self.SEPARATOR + self.__data
        return text.encode(self.ENCODING)

    @classmethod
    def from_bytes(cls, raw):
        text = raw.decode(cls.ENCODING)

        if cls.SEPARATOR not in text:
            raise ProtocolError("Invalid message format")

        command, data = text.split(cls.SEPARATOR, 1)
        return cls(command, data)

    @classmethod
    def from_user_input(cls, line):
        parts = line.split(" ", 1)

        if len(parts) == 1:
            command = parts[0]
            data = ""
        else:
            command = parts[0]
            data = parts[1]

        return cls(command, data)

    def __eq__(self, other) -> bool:
        if not isinstance(other, ProtocolMessage):
            return False
        return self.__command == other.command and self.__data == other.data

    def __repr__(self) -> str:
        return f"ProtocolMessage(command={self.__command!r}, data={self.__data!r})"

    def __str__(self) -> str:
        return f"[{self.__command}]{ProtocolMessage.SEPARATOR} {self.__data}"
