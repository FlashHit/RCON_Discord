from bf_frostbite.connection import RCONConnection

class ServerInfo:
    def __init__(self, connection, config):
        self.connection = connection
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
