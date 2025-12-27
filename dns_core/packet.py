import struct
import socket

def parse_qname(data, offset):
    labels = []
    while True:
        length = data[offset]
        if length == 0:
            offset += 1
            break
        labels.append(data[offset + 1: offset + 1 + length].decode())
        offset += length + 1
    return ".".join(labels) + ".", offset

def build_response(transaction_id, question_section, domain, ip=None):
    # Header
    if ip:
        flags = b"\x81\x80"   # QR=1, No error
        ancount = b"\x00\x01"
    else:
        flags = b"\x81\x83"   # NXDOMAIN
        ancount = b"\x00\x00"

    header = transaction_id + flags + b"\x00\x01" + ancount + b"\x00\x00" + b"\x00\x00"

    if not ip:
        return header + question_section

    # Answer
    name = b"\xc0\x0c"   # pointer to domain in question section
    type_a = struct.pack("!H", 1)
    class_in = struct.pack("!H", 1)
    ttl = struct.pack("!I", 60)
    rdlength = struct.pack("!H", 4)
    rdata = socket.inet_aton(ip)

    answer = name + type_a + class_in + ttl + rdlength + rdata
    return header + question_section + answer
