import socket
import time
import datetime
import colorlog

from service.formatter import format_time
from service.logger_conf import console_handler, logging_level

#   SERVICE

# Создание и настройка логгера
logger = colorlog.getLogger(__name__)
logger.setLevel(logging_level)

# Добавление обработчика к логгеру
logger.addHandler(console_handler)

#   SERVER

run_time = time.time_ns()   # Время запуска сервера
response_ending = '\r\n> '
isFin = False
isKill = False

# Настройки сервера
HOST = '127.0.0.1'  # Локальный адрес
PORT = 12345  # Произвольный порт

def handle_command(message):
    cmd = message

    if len(message) >= 4:
        cmd = message.split()[0]

    match cmd:
        case 'ECHO':
            words = message.split()
            return " ".join(words[1:])
        case 'TIME':  # Возвращаем текущее время сервера
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        case 'WORK_TIME':  # Возвращаем время работы сервера
            execution_time = time.time_ns() - run_time
            return format_time(execution_time)
        case 'CLOSE':  # Закрываем соединение
            global isFin
            isFin = True
            return 'Closing connection...'
        case 'KILL_ME':
            global isKill
            isFin = True
            isKill = True
            return 'Shutting down the server...'
        case _:
            return 'Unknown command'


if __name__ == '__main__':
    logger.info("Server is running")

    # Создание сокета
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Привязка сокета к адресу и порту
    server_socket.bind((HOST, PORT))

    # Ожидание подключения клиентов
    server_socket.listen(5)

    logger.info(f"Server started on {HOST}:{PORT}")

    while not isKill:
        # Принятие соединения
        client_socket, addr = server_socket.accept()
        logger.info(f"Connected by {addr}")

        client_socket.sendall((f'Connected to {HOST}:{PORT}' + response_ending).encode())

        # Обработка запросов клиента
        while True:
            # Получение данных от клиента`
            data = b''
            while True:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                if b'\r\n' in chunk:
                    break
                if b'\n' in chunk:
                    break
                data += chunk

            try:
                # Декодирование данных и обработка команды
                logger.debug(f"{addr} Received: {len(data)} bytes, Data: {data.decode()}")
                command = data.decode()
            except UnicodeDecodeError:
                logger.error(f"Error decoding. {addr} Received: {len(data)} bytes, Data: {data}")
                client_socket.sendall(('Incorrect request. Try again...' + response_ending).encode())
            else:
                response = handle_command(command)
                if not isFin:
                    response += response_ending
                client_socket.sendall(response.encode())

            # Закрытие соединения при необходимости
            if isFin:
                break

        # Закрытие соединения с клиентом
        client_socket.close()
        logger.info(f"Connection with {addr} closed")
        isFin = False
    server_socket.close()
