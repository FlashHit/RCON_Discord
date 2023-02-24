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
