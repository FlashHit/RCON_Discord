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
