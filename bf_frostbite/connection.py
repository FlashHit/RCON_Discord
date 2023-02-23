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

class ServerInfo:
    def __init__(self, config):
        self.connection = RCONConnection(config["remote_addr"], config["port"], config["pwd"])
        self.is_active = True
        self.message = None
        self.config = config
        self.server_name = ""
        self.player_count = 0
        self.max_players = 0
        self.current_gamemode = ""
        self.current_map = ""
        self.update()

    def update(self):
        if not self.is_active:
            self.connection.reconnect()

        serverInfo = self.connection.send(words=["serverInfo"])

        if not serverInfo:
            self.is_active = False
            return False

        # sometimes it reads events like ['server.onMaxPlayerCountChange', 32]
        # this check is to ignore those
        if serverInfo[0] != "OK" or len(serverInfo) < 20:
            return True

        self.is_active = True
        self.server_name = serverInfo[1]
        self.player_count = serverInfo[2]
        self.max_players = serverInfo[3]
        self.current_gamemode = serverInfo[4]
        self.current_map = serverInfo[5]
        return True
