import os
import struct
import socket

TYPE_MAP = {
    1: "A",
    2: "NS",
    5: "CNAME",
    12: "PTR",
    15: "MX",
    16: "TXT",
    28: "AAAA",
    255: "ANY",
}
TYPE_CODE = {v: k for k, v in TYPE_MAP.items()}

def parse_qname(data, offset):
    labels = []
    while True:
        length = data[offset]
        if length == 0:
            offset += 1
            break
        labels.append(data[offset + 1: offset + 1 + length].decode("ascii", "ignore"))
        offset += length + 1
    return ".".join(labels) + ".", offset

def encode_qname(name):
    if not name.endswith("."):
        name += "."
    parts = name.split(".")
    out = b""
    for part in parts:
        if not part:
            continue
        out += bytes([len(part)]) + part.encode("ascii", "ignore")
    return out + b"\x00"

def decode_qname(data, offset):
    labels = []
    jumped = False
    original_offset = offset
    while True:
        length = data[offset]
        if length == 0:
            offset += 1
            break
        if length & 0xC0 == 0xC0:
            pointer = struct.unpack("!H", data[offset:offset + 2])[0] & 0x3FFF
            if not jumped:
                original_offset = offset + 2
            offset = pointer
            jumped = True
            continue
        labels.append(data[offset + 1: offset + 1 + length].decode("ascii", "ignore"))
        offset += length + 1
    name = ".".join(labels) + "."
    return name, (original_offset if jumped else offset)

def build_query(domain, qtype_str):
    transaction_id = os.urandom(2)
    flags = b"\x01\x00"  # recursion desired
    qdcount = b"\x00\x01"
    header = transaction_id + flags + qdcount + b"\x00\x00" + b"\x00\x00" + b"\x00\x00"
    question = encode_qname(domain) + struct.pack("!HH", TYPE_CODE[qtype_str], 1)
    return transaction_id, header + question

def _build_rdata(record_type, value, priority=None):
    if record_type == "A":
        return socket.inet_aton(value)
    if record_type == "AAAA":
        return socket.inet_pton(socket.AF_INET6, value)
    if record_type in {"CNAME", "NS", "PTR"}:
        return encode_qname(value)
    if record_type == "MX":
        preference = struct.pack("!H", priority or 0)
        return preference + encode_qname(value)
    if record_type == "TXT":
        raw = value.encode("ascii", "ignore")[:255]
        return bytes([len(raw)]) + raw
    return b""

def build_response(transaction_id, question_section, answers, rcode=0):
    flags = 0x8180 if rcode == 0 else 0x8183
    header = (
        transaction_id
        + struct.pack("!H", flags)
        + b"\x00\x01"
        + struct.pack("!H", len(answers))
        + b"\x00\x00"
        + b"\x00\x00"
    )
    if not answers:
        return header + question_section

    response = header + question_section
    for answer in answers:
        name = b"\xc0\x0c"
        record_type = answer["type"]
        type_code = struct.pack("!H", TYPE_CODE[record_type])
        class_in = struct.pack("!H", 1)
        ttl = struct.pack("!I", answer.get("ttl", 60))
        rdata = _build_rdata(record_type, answer["value"], answer.get("priority"))
        rdlength = struct.pack("!H", len(rdata))
        response += name + type_code + class_in + ttl + rdlength + rdata
    return response

def parse_dns_response(data):
    transaction_id = data[:2]
    flags = struct.unpack("!H", data[2:4])[0]
    rcode = flags & 0x000F
    qdcount = struct.unpack("!H", data[4:6])[0]
    ancount = struct.unpack("!H", data[6:8])[0]
    offset = 12
    questions = []
    for _ in range(qdcount):
        name, offset = decode_qname(data, offset)
        qtype, _ = struct.unpack("!HH", data[offset:offset + 4])
        offset += 4
        questions.append({"name": name, "type": qtype})
    answers = []
    for _ in range(ancount):
        name, offset = decode_qname(data, offset)
        atype, aclass, ttl, rdlength = struct.unpack("!HHIH", data[offset:offset + 10])
        offset += 10
        rdata = data[offset:offset + rdlength]
        offset += rdlength
        record_type = TYPE_MAP.get(atype, str(atype))
        value = None
        if atype == 1 and rdlength == 4:
            value = socket.inet_ntoa(rdata)
        elif atype == 28 and rdlength == 16:
            value = socket.inet_ntop(socket.AF_INET6, rdata)
        elif atype in {2, 5, 12}:
            value, _ = decode_qname(data, offset - rdlength)
        elif atype == 15 and rdlength >= 3:
            preference = struct.unpack("!H", rdata[:2])[0]
            exchange, _ = decode_qname(data, offset - rdlength + 2)
            value = f"{preference} {exchange}"
        elif atype == 16 and rdlength >= 1:
            length = rdata[0]
            value = rdata[1:1 + length].decode("ascii", "ignore")
        answers.append(
            {
                "name": name,
                "type": record_type,
                "ttl": ttl,
                "data": value,
            }
        )
    
    result = {
        "Status": rcode,
        "TC": (flags >> 9) & 1,
        "RD": (flags >> 8) & 1,
        "RA": (flags >> 7) & 1,
        "Question": questions,
        "Answer": answers,
        "TransactionID": int.from_bytes(transaction_id, "big"),
    }
    
    
    return result
