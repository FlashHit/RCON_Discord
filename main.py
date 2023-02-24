from datetime import datetime
import bf_refractor.serverInfo as bf_refractor
import bf_frostbite.serverInfo as bf_frostbite
from bf_refractor.connection import RCONConnection as bf_refractor_RCONConnection
from bf_frostbite.connection import RCONConnection as bf_frostbite_RCONConnection
import config
import map_config
import discord
from discord.ext import tasks

def get_embed(server_info: bf_refractor.ServerInfo|bf_frostbite.ServerInfo):
    game = server_info.config["game"]
    color = server_info.is_active and discord.Color.green() or discord.Color.red()
    title = server_info.is_active and server_info.server_name or server_info.server_name + " (Offline)"
    embed = discord.Embed(title=title, color=color, timestamp=datetime.now())
    
    if server_info.is_active:
        embed.add_field(name="Players", value=f"{server_info.player_count}/{server_info.max_players}", inline=True)
        embed.add_field(name="Map", value=map_config.map_names[game].get(server_info.current_map) or server_info.current_map, inline=True)
        embed.add_field(name="GameMode", value=map_config.gamemode_names[game].get(server_info.current_gamemode) or server_info.current_gamemode, inline=True)
        if server_info.config.get("use_map_banners"):
            current_map_url = map_config.map_banners[game].get(server_info.current_map)
            if current_map_url:
                embed.set_image(url=current_map_url)
        else:
            banner_url = server_info.config["banner_url"]
            if banner_url:
                embed.set_image(url=banner_url)
        link = server_info.config.get("link")
        if link:
            embed.add_field(name="", value="<"+link+">", inline=False)

    embed.set_footer(text="Last updated")
    return embed

def run_discord_bot(TOKEN: str, server_infos: list[bf_refractor.ServerInfo|bf_frostbite.ServerInfo]):
    client = discord.Client(intents=discord.Intents.default())

    @client.event
    async def on_ready():
        """
        Initial event. Gets triggered once the discord bot is ready.
        First clear all messages in the defined discord channels.
        Then start the update loop, which will create/ update messages containing server information.
        """
        print(f'{client.user} is now running!')
        server_name = config.server_info.get("server_name")
        channel_name = config.server_info.get("channel_name")

        # clear all messages
        for server_info in server_infos:
            if server_info.config.get("clear_messages"):
                dc_server = server_info.config.get("dc_server") or server_name
                dc_channel = server_info.config.get("dc_channel")
                if dc_server and dc_channel:
                    channel = discord.utils.get(client.get_all_channels(), guild__name=dc_server, name=dc_channel)
                    await channel.purge()
        
        if config.server_info.get("clear_messages") and server_name and channel_name:
            channel = discord.utils.get(client.get_all_channels(), guild__name=server_name, name=channel_name)
            await channel.purge()
        on_update.start()

    @tasks.loop(seconds = 10)
    async def on_update():
        """
        Updates all stored ServerInfo classes as well as their message.
        Messages that don't exist will be created.
        """
        for server_info in server_infos:
            dc_server = server_info.config.get("dc_server") or config.server_info.get("server_name")
            dc_channel = server_info.config.get("dc_channel") or config.server_info.get("channel_name")
            # TODO: this should probably be async
            server_info.update()
            if server_info.message:
                await server_info.message.edit(embed=get_embed(server_info))
            elif server_info.is_active:
                channel = discord.utils.get(client.get_all_channels(), guild__name=dc_server, name=dc_channel)
                server_info.message = await channel.send(embed=get_embed(server_info))

    client.run(TOKEN)

if __name__ == '__main__':
    """
    Create all RCON connections to the defined game servers.
    Then create ServerInfo classes that process RCON commands and store some important information.
    Then create/ start the discord bot. 
    """
    server_infos = []
    for game_server in config.game_servers:
        server_info_config = game_server.get("server_info")
        if game_server["engine"] == "Refractor":
            connection = bf_refractor_RCONConnection(game_server["remote_addr"], game_server["port"], game_server["pwd"])
            if server_info_config:
                server_infos.append(bf_refractor.ServerInfo(connection, server_info_config))
        elif game_server["engine"] == "Frostbite":
            connection = bf_frostbite_RCONConnection(game_server["remote_addr"], game_server["port"], game_server["pwd"])
            if server_info_config:
                server_infos.append(bf_frostbite.ServerInfo(connection, server_info_config))

    run_discord_bot(config.TOKEN, server_infos)
