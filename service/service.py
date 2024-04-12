import re
import socket


def get_local_ip():
    try:
        # Get the local IP address associated with the first non-localhost network interface
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return None


def get_subnet(ip_address):
    elements = ip_address.split('.')
    subnet = '.'.join(elements[:3])
    return subnet + '.'


def extract_addr_port(s: str):
    match = re.match(r"a:(.*?);p:(\d+)", s)
    if match:
        addr = match.group(1)
        port = int(match.group(2))
        return addr, port
    else:
        return None, None
