from datetime import datetime
import bf_refractor
import bf_frostbite.connection as bf_frostbite
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
            embed.set_image(url=map_config.map_banners[game].get(server_info.current_map) or server_info.current_map)
        else:
            embed.set_image(url=server_info.config["banner_url"])
        link = server_info.config.get("link")
        if link:
            embed.add_field(name="", value="<"+link+">", inline=False)

    embed.set_footer(text="Last updated")
    return embed

def run_discord_bot(TOKEN: str, server_name: str, channel_name: str, server_infos: list[bf_refractor.ServerInfo|bf_frostbite.ServerInfo]):
    client = discord.Client(intents=discord.Intents.default())

    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')
        channel = discord.utils.get(client.get_all_channels(), guild__name=server_name, name=channel_name)
        # clear all messages
        if config.clear_messages:
            await channel.purge()

        for server_info in server_infos:
            if server_info.is_active:
                server_info.message = await channel.send(embed=get_embed(server_info))
        on_update.start()

    @tasks.loop(seconds = 10)
    async def on_update():
        for server_info in server_infos:
            server_info.update()
            if server_info.message:
                await server_info.message.edit(embed=get_embed(server_info))
            elif server_info.is_active:
                guild_channel = discord.utils.get(client.get_all_channels(), guild__name=server_name)
                channel = discord.utils.get(guild_channel.channels, name=channel_name)
                server_info.message = await channel.send(embed=get_embed(server_info))

    client.run(TOKEN)

if __name__ == '__main__':
    server_infos = []
    for game_server in config.game_servers:
        if game_server["engine"] == "Refractor":
            server_infos.append(bf_refractor.ServerInfo(game_server))
        elif game_server["engine"] == "Frostbite":
            server_infos.append(bf_frostbite.ServerInfo(game_server))

    run_discord_bot(config.TOKEN, config.server_name, config.channel_name, server_infos)
