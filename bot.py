import os
import sys
import re
import discord
import commands
import config
import time

from dotenv import load_dotenv

if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] != "-nd":
        time.sleep(60)

bot_pattern = re.compile(r"b! +([a-zA-Z0-9-]+) ?(.*)")
log_file = os.path.expanduser("~/otto.log")

if not os.path.isdir(os.path.join(config.root_path, 'data')):
    os.mkdir(os.path.join(config.root_path, 'data'))
if not os.path.isdir(os.path.join(config.root_path, 'tables')):
    os.mkdir(os.path.join(config.root_path, 'tables'))

load_dotenv(os.path.join(config.root_path, ".env"))
token = os.getenv('DISCORD_TOKEN')

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
    with open(log_file, 'a') as lf:
        lf.write(f'{cmd}: {args}\n')
    try:
        cmd_func = getattr(commands, f'cmd_{cmd.lower()}')
        await cmd_func(message, args)
    # except AttributeError:
    #     await commands.cmd_message(message, args)
    except Exception as e:
        with open(log_file, 'a') as lf:
            lf.write(f'{e}\n')
            lf.write(str(e.__traceback__)+'\n')

if __name__ == '__main__':
    client.run(token)
