
import gradio as gr
import threading

from NetworkClient import NetworkClient
from Protocol import Protocol
from ProtocolMessage import ProtocolMessage
from ProtocolError import ProtocolError


class GradioClientUI:

    def __init__(self, ip="127.0.0.1", port=8000):
        self.__default_ip = ip
        self.__default_port = port

        # מילון ששומר לקוח נפרד לכל משתמש
        self.__clients = {}

        # מילון ששומר שם לכל לקוח
        self.__client_names = {}

        # מספר הלקוח הבא
        self.__next_client_number = 1

        # נעילה שמגנה על המילונים
        self.__lock = threading.Lock()

        # בניית הממשק
        self.demo = self.__build()

    def __build(self):
        with gr.Blocks() as demo:

            gr.Markdown("# CyberVault - TCP Client")

            ip_input = gr.Textbox(
                label="Server IP",
                value=self.__default_ip
            )

            port_input = gr.Number(
                label="Port",
                value=self.__default_port
            )

            connect_button = gr.Button("Connect")

            disconnect_button = gr.Button(
                "Disconnect",
                interactive=False
            )

            status = gr.Textbox(
                label="Status",
                value="Disconnected",
                interactive=False
            )

            command_input = gr.Dropdown(
                choices=Protocol.COMMANDS,
                label="Command",
                value="PING",
                interactive=False
            )

            data_input = gr.Textbox(
                label="Data",
                placeholder="Enter data here...",
                interactive=False
            )

            send_button = gr.Button(
                "Send",
                interactive=False
            )

            chat_history = gr.Chatbot(
                label="Requests and replies"
            )

            clear_button = gr.Button("Clear log")

            # התחברות
            connect_event = connect_button.click(
                fn=self.__connect,
                inputs=[
                    ip_input,
                    port_input,
                    command_input,
                    chat_history
                ],
                outputs=[
                    chat_history,
                    status
                ]
            )

            connect_event.then(
                fn=self.__update_view,
                inputs=[chat_history, command_input],
                outputs=[
                    chat_history,
                    connect_button,
                    disconnect_button,
                    command_input,
                    data_input,
                    send_button
                ]
            )

            # התנתקות
            disconnect_event = disconnect_button.click(
                fn=self.__disconnect,
                inputs=[
                    command_input,
                    chat_history
                ],
                outputs=[
                    chat_history,
                    status
                ]
            )

            disconnect_event.then(
                fn=self.__update_view,
                inputs=[chat_history, command_input],
                outputs=[
                    chat_history,
                    connect_button,
                    disconnect_button,
                    command_input,
                    data_input,
                    send_button
                ]
            )

            # שליחת הודעה
            send_event = send_button.click(
                fn=self.__send,
                inputs=[
                    command_input,
                    data_input,
                    chat_history
                ],
                outputs=[
                    chat_history,
                    status,
                    data_input
                ]
            )

            send_event.then(
                fn=self.__update_view,
                inputs=[chat_history, command_input],
                outputs=[
                    chat_history,
                    connect_button,
                    disconnect_button,
                    command_input,
                    data_input,
                    send_button
                ]
            )

            # שליחה באמצעות Enter
            submit_event = data_input.submit(
                fn=self.__send,
                inputs=[
                    command_input,
                    data_input,
                    chat_history
                ],
                outputs=[
                    chat_history,
                    status,
                    data_input
                ]
            )

            submit_event.then(
                fn=self.__update_view,
                inputs=[chat_history, command_input],
                outputs=[
                    chat_history,
                    connect_button,
                    disconnect_button,
                    command_input,
                    data_input,
                    send_button
                ]
            )

            # שינוי פקודה
            command_input.change(
                fn=self.__on_command_change,
                inputs=[command_input],
                outputs=[data_input]
            )

            # ניקוי ההיסטוריה בלבד
            clear_button.click(
                fn=lambda: [],
                inputs=[],
                outputs=[chat_history]
            )

            # ניקוי החיבור כאשר המשתמש עוזב
            demo.unload(fn=self.__on_unload)

        return demo

    def launch(self, **kwargs):
        self.demo.launch(**kwargs)

    def __get_client(self, request: gr.Request):
        session_id = request.session_hash

        with self.__lock:
            return self.__clients.get(session_id)

    def __remove_client(self, request: gr.Request):
        session_id = request.session_hash

        with self.__lock:
            client = self.__clients.pop(session_id, None)
            self.__client_names.pop(session_id, None)

        if client is not None:
            client.close()

    def __on_unload(self, request: gr.Request):
        self.__remove_client(request)

    def __view(self, history, client, command, clear_data):
        connected = client is not None and client.connected

        data_update = gr.update(
            interactive=(
                connected
                and command in Protocol.COMMANDS_WITH_DATA
            )
        )

        if clear_data:
            data_update["value"] = ""

        return [
            history,
            gr.update(interactive=not connected),
            gr.update(interactive=connected),
            gr.update(interactive=connected),
            data_update,
            gr.update(interactive=connected)
        ]

    def __update_view(
        self,
        history,
        command,
        request: gr.Request
    ):
        client = self.__get_client(request)

        return self.__view(
            history,
            client,
            command,
            False
        )

    def __add(self, history, role, text):
        history = history or []

        history.append({
            "role": role,
            "content": text
        })

        return history

    def __describe(self, error):
        return str(error)

    # שינוי פקודה וניקוי תיבת הטקסט
    def __on_command_change(
        self,
        command,
        request: gr.Request
    ):
        client = self.__get_client(request)

        connected = client is not None and client.connected

        return gr.update(
            value="",
            interactive=(
                connected
                and command in Protocol.COMMANDS_WITH_DATA
            )
        )

    # התחברות לשרת ומתן שם אוטומטי ללקוח
    def __connect(
        self,
        ip,
        port,
        command,
        history,
        request: gr.Request
    ):
        session_id = request.session_hash

        try:
            client = NetworkClient(ip, int(port))

            with self.__lock:
                old_client = self.__clients.get(session_id)

                # אם זה משתמש חדש, נותנים לו מספר
                if session_id not in self.__client_names:
                    client_name = f"Client {self.__next_client_number}"

                    self.__client_names[session_id] = client_name

                    self.__next_client_number += 1

                else:
                    client_name = self.__client_names[session_id]

                # שמירת החיבור של הלקוח
                self.__clients[session_id] = client

            if old_client is not None:
                old_client.close()

            history = self.__add(
                history,
                "assistant",
                f"{client_name} connected to {ip}:{int(port)}"
            )

            return history, f"{client_name} - Connected"

        except (ValueError, TypeError, OSError, ConnectionError) as e:
            history = self.__add(
                history,
                "assistant",
                self.__describe(e)
            )

            return history, "Disconnected"

    # התנתקות מהשרת
    def __disconnect(
        self,
        command,
        history,
        request: gr.Request
    ):
        client = self.__get_client(request)

        if client is None:
            return history, "Already disconnected"

        history = self.__add(
            history,
            "user",
            "EXIT"
        )

        try:
            reply = client.request(ProtocolMessage("EXIT"))

            if reply is not None:
                history = self.__add(
                    history,
                    "assistant",
                    str(reply)
                )

        except (ProtocolError, ConnectionError, OSError) as e:
            history = self.__add(
                history,
                "assistant",
                self.__describe(e)
            )

        finally:
            self.__remove_client(request)

        return history, "Disconnected"

    # שליחת הודעה לשרת
    def __send(
        self,
        command,
        data,
        history,
        request: gr.Request
    ):
        client = self.__get_client(request)

        if client is None:
            history = self.__add(
                history,
                "assistant",
                "Please connect to the server first."
            )

            return history, "Disconnected", ""

        try:
            message = ProtocolMessage(command, data)

            history = self.__add(
                history,
                "user",
                str(message)
            )

            reply = client.request(message)

            if reply is not None:
                history = self.__add(
                    history,
                    "assistant",
                    str(reply)
                )

            if message.command == "EXIT":
                self.__remove_client(request)

                return history, "Disconnected", ""

            return history, "Connected", ""

        except (ProtocolError, ConnectionError, OSError) as e:
            history = self.__add(
                history,
                "assistant",
                self.__describe(e)
            )

            self.__remove_client(request)

            return history, "Disconnected", ""


if __name__ == "__main__":
    app = GradioClientUI()
    app.launch()
