import os
import socket
import threading
import time
import datetime
import colorlog

import service.file_manager as file_manager
from service.file_manager import get_files_and_dirs
from service.formatter import format_time
from service.logger_conf import console_handler, logging_level

# Создание и настройка логгера
logger = colorlog.getLogger(__name__)
logger.setLevel(logging_level)
# Добавление обработчика к логгеру
logger.addHandler(console_handler)

# Настройки сервера
HOST = '127.0.0.1'  # Локальный адрес
PORT = 5500  # Произвольный порт
run_time = time.time_ns()  # Время запуска сервера
response_ending = '\r\n> '


class ConnectionHandler:
    def __init__(self, client_socket, addr):
        self.client_socket = client_socket
        self.addr = addr

        logger.info(f"Connected by {addr}")
        self.send_message(f'Connected to {HOST}:{PORT}' + response_ending)
        self.is_disconnect = False

        self.root_dir = os.path.curdir + '\\resources\\server'
        self.user_dir = ''

    def start(self):
        self.listener()

    def send_message(self, message):
        try:
            self.client_socket.sendall(message.encode())
        except ConnectionRefusedError:
            logger.error(f"Connection refused")

    def handle_command(self, request):  # Обработка запросов клиента
        if not request:
            return

        command = request.split()[0].upper()
        content = " ".join(request.split()[1:])
        directory = f'{self.root_dir}\\{self.user_dir}'

        # Commands for laboratory work #1
        if 'ECHO' == command:
            self.send_message(content)
        elif 'TIME' == command:  # Возвращаем текущее время сервера
            self.send_message(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        elif 'WORK_TIME' == command:  # Возвращаем время работы сервера
            execution_time = time.time_ns() - run_time
            self.send_message(format_time(execution_time))

        # Commands for laboratory work #2
        elif 'UPLOAD' == command:  # Запрос на закачку файла на сервер
            if not content:
                self.send_message('Fail. Bad request')
                return
            file_manager.receive_file(self.client_socket, f'{directory}\\{content}')
            self.send_message('Success')
        elif 'DOWNLOAD' == command:  # Запрос на скачивание файла c сервера
            if not content:
                self.send_message('Fail. Bad request')
                return

            self.send_message('downloading...')
            file_manager.send_file(self.client_socket, f'{directory}\\{content}')
            self.send_message('download complete')

            time.sleep(0.15)
            self.send_message('Success')
        elif 'LS' == command:  # Запрос на полуение списка файлов и катологов
            logger.debug(f'Directory: {directory}')
            files, dirs = get_files_and_dirs(directory)
            logger.debug(f"files: {files}, dirs: {dirs}")

            entity_list = f"Contents of \\{self.user_dir}:"

            if self.user_dir:
                entity_list += f"\r\n.."

            for dir_name in dirs:
                entity_list += f"\r\n{dir_name}\\"
            for file_name in files:
                entity_list += f"\r\n{file_name}"

            self.send_message(entity_list)

        elif 'CD' == command:  # Запрос на переход в другой каталог
            self.send_message(f'Command "{command}" in developing...')
            pass

        # Service commands
        elif 'CLOSE' == command or 'EXIT' == command:  # Закрываем соединение
            self.is_disconnect = True
        else:
            self.send_message('Unknown command')

    def listener(self):
        while not self.is_disconnect:
            try:
                # Получение данных от клиента
                data = self.client_socket.recv(1024)
                # Декодирование данных и обработка команды
                command = data.decode()
                logger.info(f"{self.addr} Data: {data.decode()}, size: {len(data)} bytes")
            except UnicodeDecodeError:
                logger.error(f"{self.addr} Error decoding...")
                self.send_message('Incorrect request. Try again...' + response_ending)
            except ConnectionResetError:
                logger.error(f"{self.addr} The client forced the termination of an existing connection")
                break
            except ConnectionAbortedError:
                logger.warning(f"{self.addr} The connection was severed")
                break
            else:
                self.handle_command(command)
                if not self.is_disconnect:
                    self.send_message(response_ending)
                else:
                    self.disconnect()
                    break
        logger.debug('Listener stopped')

    def disconnect(self):  # Закрытие соединения с клиентом
        self.send_message('Closing connection...')
        self.send_message('\r\n')
        self.client_socket.close()
        logger.info(f"Connection with {self.addr} closed")


shutdown_server = False


def server_command_handler(command):
    cmd = command.upper()
    logger.debug(f"Server command: '{cmd}'")
    if 'SHUTDOWN' == cmd:
        global shutdown_server
        shutdown_server = True
    elif 'SHUTDOWN F' == cmd:
        os._exit(0)
    elif 'THREADS' == cmd:
        all_threads = threading.enumerate()
        counter = 0
        list_of_threads = "List of threads:"
        for thread in all_threads:
            list_of_threads += f'\r\n[{counter}] | {thread.name}'
            counter += 1
        logger.debug(list_of_threads)
    else:
        logger.warning('Server: Unknown command')


def server_input_command():
    while not shutdown_server:
        server_command_handler(input())
    logger.info(f'Server: Waiting for the end of sessions')


if __name__ == '__main__':
    logger.info("Server is running...")

    # Создание сокета
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Что здесь?
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Привязка сокета к адресу и порту
    server_socket.bind((HOST, PORT))

    # Ожидание подключения клиентов
    server_socket.listen(5)

    logger.info(f"Server started on {HOST}:{PORT}")

    server_input_listener = threading.Thread(target=server_input_command)
    server_input_listener.start()

    while not shutdown_server:
        # Принятие соединения
        client_socket, addr = server_socket.accept()
        ConnectionHandler(client_socket, addr).start()

    # while not shutdown_server:
    #     client_socket, addr = server_socket.accept()
    #     print(f"New connection from {addr}")
    #     client_thread = Thread(target=handle_client, args=(client_socket,))
    #     client_thread.start()

    logger.info(f"Shutting down...")

    server_input_listener.join(timeout=5)  # 5 sec
    server_socket.close()
