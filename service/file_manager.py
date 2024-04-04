import os
import socket
import struct
import time
import webbrowser

import colorlog

from service.logger_conf import logging_level, console_handler

# from service.logger_conf import logging_level, console_handler

# Создание и настройка логгера
logger = colorlog.getLogger(__name__)
logger.setLevel(logging_level)
# Добавление обработчика к логгеру
logger.addHandler(console_handler)


def get_files_and_dirs(directory):
    """Return a list of files and directories in the given directory."""
    entries = os.listdir(directory)
    files = [entry for entry in entries if os.path.isfile(os.path.join(directory, entry))]
    dirs = [entry for entry in entries if os.path.isdir(os.path.join(directory, entry))]
    return files, dirs


def crete_directory(dir_path):
    # Check if the directory exists
    if not os.path.exists(dir_path):
        # If the directory does not exist, create it
        os.makedirs(dir_path)


def receive_file_size(sck: socket.socket):
    fmt = "<Q"
    expected_bytes = struct.calcsize(fmt)
    received_bytes = 0
    stream = bytes()
    while received_bytes < expected_bytes:
        try:
            chunk = sck.recv(expected_bytes - received_bytes)
            stream += chunk
            received_bytes += len(chunk)
        except ConnectionResetError:  # Обрыв соединения
            logger.error("[receive_file_size] ConnectionResetError")
            break
        except OSError:
            logger.error(f"[receive_file_size] OSError")
            return 0
    filesize = struct.unpack(fmt, stream)[0]
    return filesize


def receive_file(sck: socket.socket, filename):
    laddr = sck.getsockname()
    raddr = sck.getpeername()

    filesize = receive_file_size(sck)

    logger.debug(f'Received filesize: {filesize}')

    counter = 0

    logger.debug(f'Socket before: {sck}')
    with open(filename, "wb") as f:
        received_bytes = 0
        while received_bytes < filesize:
            try:
                chunk = sck.recv(1024)
                if chunk:
                    f.write(chunk)
                    received_bytes += len(chunk)

                if chunk == b'':
                    counter += 1
                    time.sleep(0.1)
                else:
                    counter = 0

                # if counter > 0 and counter % 10 == 0:
                #     logger.debug(f'Socket atp {counter}: {sck}')

                if counter >= 50:  # Искусственый обрыв сети
                    logger.error(f"Unable to receive file")
                    logger.debug(f'Socket after:  {sck}')
                    # to-do:  delete file
                    return
            except ConnectionResetError:
                logger.error(f'[receive_file] ConnectionResetError')

                # wait reconnect
                logger.debug(f'Socket: {sck}')
                # sck = wait_reconnect(sck, laddr, raddr)
                logger.debug(f'Recovered socket: {sck}')

                if sck.fileno() != -1:
                    continue  # successfully attempt
                break  # time out
            except Exception:
                logger.error(f'[receive_file] Exception')
            # except OSError:
            #     logger.error(f'[receive_file] OSError')
            #     break  # time out


def send_file(sck: socket.socket, filename):
    # laddr = sck.getsockname()
    raddr = sck.getpeername()

    filesize = os.path.getsize(filename)

    sck.sendall(struct.pack("<Q", filesize))

    counter = 0
    attempt = 0

    logger.debug(f'Send filesize: {filesize}')
    with open(filename, "rb") as f:
        while read_bytes := f.read(1024):

            if counter >= 20:  # Искусственый обрыв сети
                logger.debug(f'Socket closed: {sck}')
                # sck.shutdown(socket.SHUT_WR)

                counter = 0
            else:
                counter += 1

            while True:
                try:
                    sck.sendall(read_bytes)
                    attempt = 0
                    break
                except socket.error:
                    logger.error(f'[send_file] Exception')

                    # attempt to reconnect
                    # logger.debug(f'Socket: {sck}')
                    attempt += 1
                    if attempt >= 35:
                        logger.debug(f'[send_file] Successfully attempt #{attempt}')
                        sck.shutdown(socket.SHUT_RD)
                        # sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        # sck.bind(raddr)
                    else:
                        logger.debug(f'[send_file] Bad attempt #{attempt}')
                        time.sleep(0.1)

                    # sck = reconnect(sck, laddr, raddr)

                    # time.sleep(0.1)

                    if attempt >= 50:
                        # os._exit(1)
                        return
                    continue

                    # if sck.fileno() != -1:
                    #     continue  # successfully attempt
                    # return  # time out


def wait_reconnect(sck: socket.socket, laddr, raddr, time_out=15) -> socket.socket:
    if sck.fileno() != -1:
        sck.close()

    logger.debug(f'sck: {sck}')

    start_time = time.time()
    logger.debug(f'[wr] Waiting for reconnect. Time: {start_time}, Time out: {start_time + time_out}')

    while start_time + time_out > time.time():
        if sck.fileno() == -1:
            sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            if sck.getsockname() != laddr:
                sck.bind(laddr)
        except OSError:
            sck.bind(laddr)

        logger.debug(f'[wr] Socket: {sck}')

        if sck.getpeername() != raddr:
            sck.listen()
            addr = sck.accept()

            if addr != raddr:
                logger.debug(f'[wr] Incorrect socket connection: {sck}')
                sck.close()
                continue
            else:
                logger.debug(f'[wr] Correct socket connection: {sck}')
                return sck
        else:
            return sck
    sck.close()
    return sck


def reconnect(sck: socket.socket, laddr, raddr, attempts=4) -> socket.socket:
    logger.debug(f'[r] Waiting for reconnect. Attempts: {attempts}')

    for i in range(attempts):
        if sck.fileno() == -1:
            sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            if sck.getsockname() != laddr:
                sck.bind(laddr)
        except OSError:
            sck.bind(laddr)

        logger.debug(f'[r] Socket: {sck}')
        logger.debug(f'[r] Attempt #{i + 1} connect to {raddr}')

        try:
            sck.connect(raddr)
            logger.debug(f'[r] Success attempt: {sck}')
            return sck

        except ConnectionRefusedError:
            logger.debug(f'[r] Can\'t to connect to {raddr}')
        except OSError:
            logger.error(f'[reconnect] OSError')

        time.sleep(0.5)

    sck.close()
    return sck


# Function to open the file explorer to a specific path
def open_explorer(path):
    if os.name == 'nt':  # Windows
        os.startfile(path)
    else:  # Other platforms
        webbrowser.open('file://' + path.replace('\\', '/'))
