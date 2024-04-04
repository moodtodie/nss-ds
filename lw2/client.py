import os
import threading
import time
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import socket

import colorlog

import service.file_manager as file_manager
from service.logger_conf import logging_level, console_handler
from service.service import get_subnet, get_local_ip

# Создание и настройка логгера
logger = colorlog.getLogger(__name__)
logger.setLevel(logging_level)
# Добавление обработчика к логгеру
logger.addHandler(console_handler)


class ClientApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Client")
        self.is_connected = False
        self.is_downloading = False

        # ==============================================================================================================
        self.label_server = tk.Label(self, text="Server settings", font=("Helvetica", 12))
        self.label_server.grid(row=0, column=0, columnspan=5, sticky=tk.N + tk.S + tk.E + tk.W, pady=10)

        self.socket = None

        # Server IP address field
        self.server_ip_address_entry = ttk.Entry(self, width=45)
        self.server_ip_address_entry.insert(0, get_subnet(get_local_ip()))
        self.server_ip_address_entry.grid(row=1, column=1, columnspan=2, sticky=tk.N + tk.S + tk.E + tk.W, pady=10,
                                          padx=(0, 10))

        # Server port field
        self.server_port_entry = ttk.Entry(self, width=15)
        self.server_port_entry.insert(0, '5500')
        self.server_port_entry.grid(row=1, column=3, sticky=tk.N + tk.S + tk.E + tk.W, pady=10)

        # Set connection for server button
        self.send_command_button = ttk.Button(self, text="Set connection",
                                              command=self.set_server_address_and_port)
        # self.send_command_button = ttk.Button(self, text="Set connection",
        #                                       command=lambda: self.set_server_address_and_port())
        self.send_command_button.grid(row=1, column=4, sticky=tk.N + tk.S + tk.E + tk.W, pady=10, padx=10)

        # ==============================================================================================================
        self.label_command = tk.Label(self, text="Command prompt", font=("Helvetica", 12))
        self.label_command.grid(row=2, column=0, columnspan=5, sticky=tk.N + tk.S + tk.E + tk.W, pady=10)

        # Command text field
        self.command_entry = ttk.Entry(self, width=75)
        self.command_entry.config(state='disabled')
        self.command_entry.grid(row=3, column=0, columnspan=5, sticky=tk.N + tk.S + tk.E + tk.W, pady=10, padx=10)
        self.command_entry.bind("<Return>", lambda event: self.send_message(self.command_entry))

        # ==============================================================================================================
        self.label_file = tk.Label(self, text="File", font=("Helvetica", 12))
        self.label_file.grid(row=4, column=0, columnspan=5, sticky=tk.N + tk.S + tk.E + tk.W, pady=10)

        # File name
        self.file_path_entry = ttk.Entry(self, width=60)
        self.file_path_entry.grid(row=5, column=0, columnspan=3, sticky=tk.N + tk.S + tk.E + tk.W, pady=10, padx=10)
        self.file_path_entry.insert(tk.END, 'D:/Projects/bsuir/term6/NSS&DS/lw2/resources/client/уа.jpg')
        self.root_dir = os.path.curdir + '\\resources\\client'
        file_manager.crete_directory(self.root_dir)
        # self.file_path_entry.disabled()

        # Choose a file button
        self.button = ttk.Button(self, text="Choose a file", command=self.open_file_dialog)
        self.button.grid(row=5, column=3, sticky=tk.N + tk.S + tk.E + tk.W, pady=10)

        # Send file button
        self.button = ttk.Button(self, text="Downloads", command=self.open_downloads)
        self.button.grid(row=5, column=4, sticky=tk.N + tk.S + tk.E + tk.W, pady=10, padx=10)

        # ==============================================================================================================
        self.label_log = tk.Label(self, text="Connection log:", font=("Helvetica", 12))
        self.label_log.grid(row=6, column=0, columnspan=5, sticky=tk.N + tk.S + tk.E + tk.W, pady=10)

        self.log_widget = tk.Text(self, width=75, height=10, wrap='word')
        self.log_widget.config(state='disabled')
        self.log_widget.grid(row=7, column=0, rowspan=3, columnspan=5, sticky=tk.N + tk.S + tk.E + tk.W, pady=10,
                             padx=10)

        # ==============================================================================================================
        self.listener_thread = threading.Thread(target=self.listener)
        self.listener_thread.start()

    def set_server_address_and_port(self):
        ip_address = self.server_ip_address_entry.get()
        port = int(self.server_port_entry.get())

        logger.debug(f'Attention connect to {ip_address}:{port}')

        if self.is_connected:
            self.disconnect()
            time.sleep(0.5)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_address = (ip_address, port)  # Server address and port
        try:
            self.socket.connect(server_address)
            self.is_connected = True
            self.command_entry.config(state='normal')

            logger.debug(f'Connected to {ip_address}:{port}')
        except ConnectionRefusedError:
            logger.debug(f'Failed attempt to connect to {ip_address}:{port}')
            self.show_notification("Error", f"Can't connect to {ip_address}:{port}...")
        # except OSError:
        #     logger.error(f'Unsuccessful attempt to connect to {ip_address}:{port}')
        #     self.show_notification("Error", f"Unsuccessful attempt to connect to {ip_address}:{port}.\n"
        #                                     f"Check ip address and port are correct.")

    def reconnect(self, time_out=10):
        # attempts to reconnect
        for i in range(time_out):
            time.sleep(1)  # fail attempt

            self.set_server_address_and_port()
            if self.is_connected:
                return True  # success attempt
        return False  # time out

    @staticmethod
    def clear_entry(entry_widget):
        """Clear the content of the given entry widget."""
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, '')

    def send_selected_file(self):
        if not self.is_connected:
            logger.error(f'Error: Unable to send a file. There is no connection.')
            self.show_notification("Error", f"Unable to send a file.\n"
                                            f"Check your connection and try again.")
            return -1

        file_path = self.file_path_entry.get()
        if not file_path:
            logger.warning("No file selected")
            self.show_notification('Error', 'Unable to send file.\nFile not selected.')
            return -1

        if not os.path.exists(file_path):
            logger.warning("File does not exist")
            self.show_notification('Error', 'File does not exist.\nCheck file path and try again.')
            return -1

        if not os.path.isfile(file_path):
            logger.warning("Not a file was selected")
            self.show_notification('Error', 'Not a file was selected.\nCheck file path and try again.')
            return -1

        return 0

    def open_file_dialog(self):
        """Open a file chooser dialog and print the selected file path."""
        file_path = filedialog.askopenfilename(title="Choose a file")
        self.clear_entry(self.file_path_entry)

        self.file_path_entry.insert(0, file_path)
        self.file_path_entry.xview(tk.END)

        logger.info(f"Selected file: {file_path}")

    def open_downloads(self):
        file_manager.open_explorer(self.root_dir)

    def handle_sent_message(self, message):
        command = message.split()[0].upper()
        arguments = " ".join(message.split()[1:])
        if command == "UPLOAD":
            file_manager.send_file(self.socket, self.file_path_entry.get())
        elif command == "DOWNLOAD":
            logger.debug("Downloading started")
            file_manager.receive_file(self.socket, f'{self.root_dir}\\{arguments}')
            logger.debug("Downloading finished")

            response = self.socket.recv(1024)

            if response == b'download complete':
                self.is_downloading = False
            logger.info(f"Download complete")
            # if message == command:
            #     self.show_notification('Error',
            #                            f'Unknown command. It is necessary to specify file names after \'{command}\'')

    def send_message(self, message_entry):
        """Send a message to the server."""
        message = message_entry.get()
        try:
            sent = self.socket.sendall(message.encode())
            logger.info(f'Sending message: {message}')

            if sent == 0:
                print("Server has closed the connection")
                self.disconnect()

            self.append_to_log(f'{message}\n')

            self.handle_sent_message(message)
        # except OSError:
        #     logger.error(f'OSError: Unable to send a "{message}"')
        #     self.show_notification("Error", f"Can't send a \"{message}\" message.\n"
        #                                     f"Check your connection and try again.")
        except AttributeError:
            logger.error(f"AttributeError: 'NoneType' object has no attribute 'encode'")
        else:
            self.clear_entry(message_entry)
        message_entry.focus_set()

    @staticmethod
    def show_notification(title, message):
        """Show a pop-up notification."""
        messagebox.showinfo(title, message)

    def listener(self):
        """Listen for connections."""
        counter = 0
        while True:
            try:
                if self.is_connected:
                    # Receive data from the server
                    response = self.socket.recv(1024)

                    # if response == b'downloading...':
                    #     self.is_downloading = True
                    #     while self.is_downloading:
                    #         time.sleep(0.1)
                    #     continue

                    logger.debug(f"Received from server: {response}")
                    self.append_to_log(f'{response.decode()}')

                    # Handle closing connection command
                    if response == b'Closing connection...':
                        self.append_to_log('\r\n')
                        self.disconnect()

                    # Handle closing connection
                    if response == b'':
                        if counter > 10:
                            self.disconnect()
                        else:
                            counter += 1
                            time.sleep(0.5)
                    else:
                        counter = 0
            except OSError:
                logger.error(f'[listener] OSError')
                self.disconnect()

    def append_to_log(self, message):
        self.log_widget.config(state='normal')
        self.log_widget.insert(tk.END, message)
        self.log_widget.yview(tk.END)
        self.log_widget.config(state='disabled')

    def disconnect(self):
        if not self.is_connected:
            return
        self.socket.close()
        self.command_entry.config(state='disabled')
        self.is_connected = False
        logger.info(f"Connection has been closed.")
        try:
            self.append_to_log('Connection has been closed.\n\n')
        except tk.TclError:
            pass


if __name__ == "__main__":
    app = ClientApp()
    app.mainloop()
    app.disconnect()

    time.sleep(0.3)
    os._exit(0)
