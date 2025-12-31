import socket
from .resolver import resolve_dns
from .logger import log_system_event

DNS_PORT = 8053

def start_udp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", DNS_PORT))
    print(f"UDP DNS server listening on port {DNS_PORT}")
    log_system_event('server_start', f'UDP DNS server started on port {DNS_PORT}')

    while True:
        data, addr = sock.recvfrom(512)
        client_ip = addr[0]
        response = resolve_dns(data, client_ip=client_ip, source='udp')
        sock.sendto(response, addr)

if __name__ == "__main__":
    start_udp_server()
