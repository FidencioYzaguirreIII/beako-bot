import os
import re
import discord
import commands

from dotenv import load_dotenv

bot_pattern = re.compile(r"b! +([a-zA-Z0-9-]+) ?(.*)")

root_path = "/home/Otto-Bot/Bot_Code/heretics-bot/"

if not os.path.isdir(os.path.join(root_path, 'data')):
    os.mkdir(os.path.join(root_path, 'data'))
if not os.path.isdir(os.path.join(root_path, 'tables')):
    os.mkdir(os.path.join(root_path, 'tables'))

load_dotenv(os.path.join(root_path, ".env"))
token = os.env('DISCORD_TOKEN')

client = discord.Client()


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord.')
    for g in client.guilds:
        print(f'Connected to: {g.name} :id={g.id}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    m = bot_pattern.match(message.content.lower())
    if not m:
        return
    cmd = m.group(1)
    args = m.group(2)
    print(f'Command: {cmd} Args: {args}')
    try:
        cmd_func = getattr(commands, f'cmd_{cmd.lower()}')
        await cmd_func(message, args)
    except AttributeError as e:
        await message.channel.send('Command not recognized, please use' +
                                   'help command to get the list.')
        raise e


if __name__ == '__main__':
    client.run(token)
