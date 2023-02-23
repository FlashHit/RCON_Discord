import socket
import hashlib

class RCONConnection:
    def __init__(self, ip, port, pwd):
        self.remote_addr = ip
        self.port = port
        self.pwd = pwd
        self.reconnect()

    def reconnect(self):
        self.socket = connect(self.remote_addr, self.port)
        self.ready = self.socket and login(self.socket, self.pwd)

    def getResponseFor(self, list_to_send: list):
        if not self.ready:
            return False

        response = invoke(self.socket, list_to_send)
        
        if not response:
            self.ready = False
        
        return response

def connect(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((ip, port))

    except socket.error or socket.herror or socket.gaierror:
        return False

    return sock

def login(sock: socket.socket, password):
    data = ""
	
    while not "\n\n" in data:
        try:
            data += sock.recv(4096).decode()

        except socket.error or socket.herror or socket.gaierror:
            return False

    index = data.find("### Digest seed: ")
    if index == -1: return False

    m = hashlib.md5()
    m.update(data[index + 17:data.find('\n', index)].encode())
    m.update(password.encode())
    pwhash = m.hexdigest()

    response = invoke(sock, "login {0}".format(pwhash))
    if response and ("Authentication success" in response):
        return True

    return False

def invoke(sock, msg):
    return _recv(sock) if _send(sock, "\x02{0}\n".format(msg)) else False

def _send(sock: socket.socket, msg: str):
    try:
        sock.sendall(msg.encode())

    except socket.error or socket.herror or socket.gaierror:
        return False

    return True

def _recv(sock):
    data = ""
    while not '\x04' in data:
        try:
            data += sock.recv(4096).decode()

        except socket.error or socket.herror or socket.gaierror:
            return False

    return data[:data.find('\x04')]

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

        initial_response = self.connection.getResponseFor("exec sv.serverName")
        
        if not initial_response:
            self.is_active = False
            return False

        self.is_active = True
        self.server_name = initial_response[:-1]
        self.max_players = int(self.connection.getResponseFor("exec sv.maxPlayers")[:-1])
        self.get_current_map()
        self.get_player_count()
        return True
    
    def get_current_map(self):
        current_map_index = self.connection.getResponseFor("exec maplist.currentMap")[:-1]
        current_map_list = self.connection.getResponseFor("exec maplist.list")[:-1]
        string_start_index = current_map_list.find(current_map_index)
        current_map_info = current_map_list[string_start_index:]
        end_index = current_map_info.find("\n")
        current_map_info = current_map_info[: end_index]

        # get the current map name
        current_map_info = current_map_info[4:]
        end_index = current_map_info.find('"')
        self.current_map = current_map_info[:end_index]

        # get the current game mode name
        current_map_info = current_map_info[end_index+2:]
        end_index = current_map_info.find(" ")
        self.current_gamemode = current_map_info[:end_index]

    def get_player_count(self):
        player_list = self.connection.getResponseFor("exec admin.listPlayers")[:-1]
        self.bot_count = player_list.count("is an AI bot.")
        self.player_count = player_list.count("Id:") - self.bot_count
