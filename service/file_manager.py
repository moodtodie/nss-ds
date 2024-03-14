import os
import socket
import struct
import webbrowser


def get_files_and_dirs(directory):
    """Return a list of files and directories in the given directory."""
    entries = os.listdir(directory)
    files = [entry for entry in entries if os.path.isfile(os.path.join(directory, entry))]
    dirs = [entry for entry in entries if os.path.isdir(os.path.join(directory, entry))]
    return files, dirs


def receive_file_size(sck: socket.socket):
    fmt = "<Q"
    expected_bytes = struct.calcsize(fmt)
    received_bytes = 0
    stream = bytes()
    while received_bytes < expected_bytes:
        chunk = sck.recv(expected_bytes - received_bytes)
        stream += chunk
        received_bytes += len(chunk)
    filesize = struct.unpack(fmt, stream)[0]
    return filesize


def receive_file(sck: socket.socket, filename):
    filesize = receive_file_size(sck)
    with open(filename, "wb") as f:
        received_bytes = 0
        while received_bytes < filesize:
            chunk = sck.recv(1024)
            if chunk:
                f.write(chunk)
                received_bytes += len(chunk)


def send_file(sck: socket.socket, filename):
    filesize = os.path.getsize(filename)

    sck.sendall(struct.pack("<Q", filesize))

    with open(filename, "rb") as f:
        while read_bytes := f.read(1024):
            sck.sendall(read_bytes)


# Function to open the file explorer to a specific path
def open_explorer(path):
    if os.name == 'nt':  # Windows
        os.startfile(path)
    else:  # Other platforms
        webbrowser.open('file://' + path.replace('\\', '/'))
