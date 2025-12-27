import socket
import struct
from udp_server import build_dns_response

DNS_PORT = 8053


def start_tcp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", DNS_PORT))
    sock.listen(5)

    print(f"TCP DNS server listening on port {DNS_PORT}")

    while True:
        conn, addr = sock.accept()
        try:
            # Read first 2 bytes (length)
            length_data = conn.recv(2)
            if not length_data:
                conn.close()
                continue

            length = struct.unpack("!H", length_data)[0]

            # Read DNS packet
            data = b""
            while len(data) < length:
                chunk = conn.recv(length - len(data))
                if not chunk:
                    break
                data += chunk

            response = build_dns_response(data)

            # Send response with length prefix
            conn.sendall(struct.pack("!H", len(response)) + response)

        finally:
            conn.close()


if __name__ == "__main__":
    start_tcp_server()
