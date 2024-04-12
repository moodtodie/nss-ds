import os
import socket
import struct
import time
import webbrowser

import colorlog

from service.logger_conf import logging_level, console_handler

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
    filesize = receive_file_size(sck)

    logger.debug(f'Received filesize: {filesize}')

    attempt = 0
    counter = 0

    logger.debug(f'Socket before: {sck}')
    with open(filename, "wb") as f:
        received_bytes = 0
        logger.debug(f'Starting receiving')
        while received_bytes < filesize:
            try:
                chunk = sck.recv(1024)
                if chunk:
                    f.write(chunk)
                    received_bytes += len(chunk)
                    counter += 1  # DEBUG
                    logger.debug(f'[{counter}] Received chunk has been write. Chunk: {chunk}')

                if chunk == b'' or not chunk:
                    attempt += 1
                    time.sleep(0.1)
                else:
                    attempt = 0

                if attempt >= 50:
                    logger.error(f"Unable to receive file")
                    break
            except Exception as e:
                attempt += 1
                logger.error(f'[receive_file] Exception: {e}')

                if attempt >= 10:
                    logger.error(f"Unable to receive file")
                    attempt += 50
                    break
        logger.debug(f'Ending receiving')

    if attempt >= 50:
        if os.path.isfile(filename):
            # os.remove(filename)
            logger.info("File deleted.")
        else:
            logger.warning("File not found.")


def send_file(sck: socket.socket, filename):
    filesize = os.path.getsize(filename)

    sck.sendall(struct.pack("<Q", filesize))

    counter = 0
    attempt = 0

    logger.debug(f'Send filesize: {filesize}')
    with open(filename, "rb") as f:
        while read_bytes := f.read(1024):
            while True:
                try:
                    sck.sendall(read_bytes)
                    attempt = 0
                    counter += 1
                    logger.debug(f'[{counter}] Send chunk. Chunk: {read_bytes}')
                    break
                except socket.error:
                    logger.error(f'[send_file] Exception')

                    # attempt to reconnect
                    attempt += 1
                    if attempt >= 35:
                        logger.debug(f'[send_file] Successfully attempt #{attempt}')
                    else:
                        logger.debug(f'[send_file] Bad attempt #{attempt}')
                        time.sleep(0.1)
                    if attempt >= 50:
                        return
                    continue


# Function to open the file explorer to a specific path
def open_explorer(path):
    if os.name == 'nt':  # Windows
        os.startfile(path)
    else:  # Other platforms
        webbrowser.open('file://' + path.replace('\\', '/'))
