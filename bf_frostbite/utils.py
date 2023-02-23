import hashlib
from struct import pack, unpack

DEFAULT_HEADER_SIZE = 12

def generate_password_hash(password: str, salt: bytes):
    m = hashlib.md5(salt)
    m.update(password.encode("latin1"))
    return m.hexdigest()

def calculate_packet_size(words):
    return DEFAULT_HEADER_SIZE + sum([len(str(word)) + 5 for word in words])

def contains_complete_packet(buf):
    return not (len(buf) < 8 or len(buf) < decode_int32(buf[4:8]))

def create_packet(sequence, is_from_server, is_response, words):
    packet = {
        "sequence": sequence,
        "is_from_server": is_from_server,
        "is_response": is_response,
        "total_words_length": len(words),
        "size": calculate_packet_size(words),
        "words": words,
    }
    return packet

def decode_int32(buf):
    return unpack("<I", buf)[0]

def decode_words(buf):
    size = decode_int32(buf[4:8])
    words = []
    offset = DEFAULT_HEADER_SIZE

    while offset < size:
        word_length = decode_int32(buf[offset : offset + 4])
        word = buf[offset + 4 : offset + 4 + word_length]
        word_str = str(word, "latin1")
        if word_str.isdigit():
            words.append(int(word_str))
        elif word_str == "true":
            words.append(True)
        elif word_str == "false":
            words.append(False)
        else:
            words.append(word_str)

        offset += word_length + 5

    return words

def decode_header(buf):
    header = decode_int32(buf[0:4])
    return {
        "sequence": header & 0x3FFFFFFF,
        "is_response": header & 0x40000000 > 0,
        "is_from_server": header & 0x80000000 > 0,
        "size": decode_int32(buf[4:8]),
        "total_words_length": decode_int32(buf[8:12]),
    }

def decode_packet(buf):
    header = decode_header(buf)
    words = decode_words(buf)
    packet = dict(header)
    packet.update(dict(words=words))
    return packet

def encode_int32(num):
    return pack("<I", num)

def encode_header(packet):
    header = packet["sequence"] & 0x3FFFFFFF
    if packet["is_from_server"]:
        header += 0x80000000
    if packet["is_response"]:
        header += 0x40000000
    return (
        encode_int32(header)
        + encode_int32(packet["size"])
        + encode_int32(packet["total_words_length"])
    )

def encode_words(packet):
    words = packet["words"]
    encoded_words = b""
    for word in words:
        word = str(word)
        encoded_words += encode_int32(len(word))
        encoded_words += word.encode("latin1")
        encoded_words += b"\x00"
    return encoded_words

def encode_packet(packet):
    encoded_header = encode_header(packet)
    encoded_words = encode_words(packet)
    return encoded_header + encoded_words
