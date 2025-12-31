import socket
import struct
from .resolver import resolve_dns
from .logger import log_system_event

DNS_PORT = 8053

def start_tcp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", DNS_PORT))
    sock.listen(5)
    print(f"TCP DNS server listening on port {DNS_PORT}")
    log_system_event('server_start', f'TCP DNS server started on port {DNS_PORT}')

    while True:
        conn, addr = sock.accept()
        try:
            length_data = conn.recv(2)
            if not length_data:
                conn.close()
                continue
            length = struct.unpack("!H", length_data)[0]
            data = b""
            while len(data) < length:
                chunk = conn.recv(length - len(data))
                if not chunk:
                    break
                data += chunk
            client_ip = addr[0]
            response = resolve_dns(data, client_ip=client_ip, source='tcp')
            conn.sendall(struct.pack("!H", len(response)) + response)
        finally:
            conn.close()

if __name__ == "__main__":
    start_tcp_server()
