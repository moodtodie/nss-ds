import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import socket

import colorlog

from service.logger_conf import logging_level, console_handler

# Создание и настройка логгера
logger = colorlog.getLogger(__name__)
logger.setLevel(logging_level)
# Добавление обработчика к логгеру
logger.addHandler(console_handler)


class ClientApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Client")
        # self.geometry("600x400")

        # ==============================================================================================================
        self.label_server = tk.Label(self, text="Server settings", font=("Helvetica", 12))
        self.label_server.grid(row=0, column=0, columnspan=5, sticky=tk.N + tk.S + tk.E + tk.W, pady=10)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connection status
        self.label_server = tk.Label(self, text="Disconnected")
        self.label_server.grid(row=1, column=0, sticky=tk.N + tk.S + tk.E + tk.W, padx=10)

        # Server IP address field
        self.server_ip_address_entry = ttk.Entry(self, width=45)
        self.server_ip_address_entry.grid(row=1, column=1, columnspan=2, sticky=tk.N + tk.S + tk.E + tk.W, padx=(0, 10))

        # Server port field
        self.server_port_entry = ttk.Entry(self, width=15)
        self.server_port_entry.grid(row=1, column=3, sticky=tk.N + tk.S + tk.E + tk.W)

        # Set connection for server button
        self.send_command_button = ttk.Button(self, text="Set connection",
                                              command=lambda: self.set_server_address_and_port('localhost', 5500))
        self.send_command_button.grid(row=1, column=4, sticky=tk.N + tk.S + tk.E + tk.W, padx=10)

        # ==============================================================================================================
        self.label_command = tk.Label(self, text="Communicate with server", font=("Helvetica", 12))
        self.label_command.grid(row=2, column=0, columnspan=5, sticky=tk.N + tk.S + tk.E + tk.W, pady=10)

        # Command text field
        self.command_entry = ttk.Entry(self, width=75)
        self.command_entry.grid(row=3, column=0, columnspan=5, sticky=tk.N + tk.S + tk.E + tk.W, padx=10)
        self.command_entry.bind("<Return>", lambda event: self.send_message(self.command_entry))

        # ==============================================================================================================
        self.label_file = tk.Label(self, text="File:", font=("Helvetica", 12))
        self.label_file.grid(row=4, column=0, columnspan=5, sticky=tk.N + tk.S + tk.E + tk.W, pady=10)

        # File name
        self.file_path_entry = ttk.Entry(self, width=60)
        self.file_path_entry.grid(row=5, column=0, columnspan=4, sticky=tk.N + tk.S + tk.E + tk.W, padx=(10, 0))
        # self.file_path_entry.disabled()

        # Choose a file button
        self.button = ttk.Button(self, text="Choose a file", command=self.open_file_dialog)
        self.button.grid(row=5, column=4, columnspan=1, sticky=tk.N + tk.S + tk.E + tk.W, pady=10, padx=10)

    def set_server_address_and_port(self, ip_address, port):
        server_address = (ip_address, port)  # Server address and port
        try:
            self.socket.connect(server_address)
            logger.debug(f'Connected to {ip_address}:{port}')
        except ConnectionRefusedError:
            logger.debug(f'Failed attempt to connect to {ip_address}:{port}')
            self.show_notification("Error", f"Can't connect to {ip_address}:{port}...")

    def clear_entry(self, entry_widget):
        """Clear the content of the given entry widget."""
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, '')

    def send_message(self, message_entry):
        """Send a message to the server."""
        message = message_entry.get()
        self.clear_entry(message_entry)
        message_entry.focus_set()
        logger.info(f'Sending message: {message}')
        self.socket.sendall(message.encode())

    def show_notification(self, title, message):
        """Show a pop-up notification."""
        messagebox.showinfo(title, message)

    def open_file_dialog(self):
        """Open a file chooser dialog and print the selected file path."""
        file_path = filedialog.askopenfilename(title="Choose a file")
        logger.info(f"Selected file: {file_path}")


if __name__ == "__main__":
    app = ClientApp()
    app.mainloop()
