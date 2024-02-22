# Необходимо реализовать простейшую программу-сервер с использованием протокола TCP.
#
# Сервер должен поддерживать выполнение нескольких комманд, определяемых на усмотрение студента,
# но как минимум должен поддерживать выполнение следующих (или аналогичных):
#
# ECHO (возвращает данные переданные клиентом после команды),
# TIME (возвращает текущее время сервера),
# CLOSE (EXIT/QUIT) (закрывает соединение).
#
# Комманда может иметь параметры (например ECHO). Любая команда должна оканчиваться символами \r\n или \n.

# В качестве клиента предполагается использование системных утилит: telnet, netcat и других.
# Возможно использование собственной программы клиента, но это является не обязательным.
#
# Продемонстрировать использование утилит:
#   nmap -- сканирование портов сервера,
#   netstat -- список открытых сокетов на сервере, номера портов.

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

# Время запуска сервера
run_time = time.time_ns()


#   SERVER

# Настройки сервера
HOST = '127.0.0.1'  # Локальный адрес
PORT = 12345        # Произвольный порт

isFin = False

def handle_command(message):
    command = message.split()[0]
    match command:
        case 'ECHO':
            words = message.split()
            return " ".join(words[1:])
        case 'TIME':    # Возвращаем текущее время сервера
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        case 'WORK_TIME':   # Возвращаем время работы сервера
            execution_time = time.time_ns() - run_time
            return format_time(execution_time)
        case 'CLOSE':    # Закрываем соединение
            isFin = True
            return 'Closing connection...'
        case _: return 'Unknown command'


if __name__ == '__main__':
    logger.info("Server is running")

    # Создание сокета
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Привязка сокета к адресу и порту
    server_socket.bind((HOST, PORT))

    # Ожидание подключения клиентов
    server_socket.listen(5)
    logger.info(f"Server started on {HOST}:{PORT}")

    while True:
        # Принятие соединения
        client_socket, addr = server_socket.accept()
        logger.info(f"Connected by {addr}")

        # Обработка запросов клиента
        while True:
            # Получение данных от клиента
            data = client_socket.recv(1024)
            if not data:
                break

            # Декодирование данных и обработка команды
            command = data.decode()
            response = handle_command(command)

            # Отправка ответа клиенту
            client_socket.sendall(response.encode())

            # Закрытие соединения при необходимости
            if isFin:
                break

        # Закрытие соединения с клиентом
        client_socket.close()
        logger.info(f"Connection with {addr} closed")
