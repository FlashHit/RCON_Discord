import binascii
import socket

from bf_frostbite.utils import (
    generate_password_hash,
    create_packet,
    contains_complete_packet,
    decode_packet,
    encode_packet,
)

class RCONConnection:
    def __init__(self, remote_addr, port, password=None, recv_buffer=1024):
        self._remote_addr = remote_addr
        self._port = port
        self._password = password
        self._conn = None
        self._authenticated = False
        self._seq = 0
        self.recv_buffer = int(recv_buffer)
        self.reconnect()

    def _read_response(self):
        data_buffer = bytes()
        while not contains_complete_packet(data_buffer):
            try:
                data_buffer += self._conn.recv(self.recv_buffer)
            except socket.error or socket.herror or socket.gaierror:
                return False

        return decode_packet(data_buffer)

    def send(self, words):
        packet_to_send = encode_packet(
            create_packet(self._seq, False, False, words=words)
        )
        self._seq += 1

        try:
            self._conn.send(packet_to_send)
        except socket.error or socket.herror or socket.gaierror:
            return False

        data = self._read_response()

        if not data:
            return False

        return data["words"]

    def reconnect(self):
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            self._conn.connect((self._remote_addr, self._port))
        except socket.error or socket.herror or socket.gaierror:
            return False
        
        self._seq = 0
        self.login()

    def login(self):
        if not self._password:
            return False

        password_salt_response = self.send(words=["login.hashed"])

        if "OK" not in password_salt_response:
            return False

        salt_bytes = binascii.unhexlify(password_salt_response[1])

        pwd_hash = generate_password_hash(password=self._password, salt=salt_bytes)
        pwd_hash_final = pwd_hash.upper()

        response = self.send(words=["login.hashed", pwd_hash_final])

        if "OK" not in response:
            return False

        self._authenticated = True

        return True

    def disconnect(self):
        if self._conn:
            self._conn.close()
            self._conn = None
            self._authenticated = False

    def read_events(self):
        self.send(words=["admin.eventsEnabled", "true"])

        while True:
            raw = self._read_response()
            yield raw["words"]
