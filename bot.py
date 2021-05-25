import os
import sys
import re
import asyncio
import discord
import commands
import config
import time
import scrapper

from dotenv import load_dotenv

if __name__ == "__main__":
    # delay just in case internet isn't connected at startup.
    if len(sys.argv) == 1 or sys.argv[1] != "-nd":
        time.sleep(60)

ncode_pattern = re.compile(r'(https?://)?(ncode.syosetu.com/?)?([a-z0-9]+)/([0-9]+)/?')
bot_pattern = re.compile(r"b! +([a-zA-Z0-9-]+) ?(.*)")
log_file = os.path.expanduser("~/otto.log")
TEMP_FILE = os.path.join(config.root_path, '.temp_file')

inform_guilds = [802505736218214420]  # my test server
#inform_guilds = [772947291606614026]  # Heretics

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
    if '-m' in sys.argv:
        # meaning manually reply.
        rep = input("Enter reply<default>: ")
        if rep.strip():
            await message.reply(rep)
            return
    try:
        cmd_func = getattr(commands, f'cmd_{cmd.lower()}')
        await cmd_func(message, args)
    except AttributeError:
        await commands.cmd_message(message, args)
    except Exception as e:
        with open(log_file, 'a') as lf:
            lf.write(f'{e}\n')
        print(f"Error logged to {log_file}")
            # lf.write(str(e.__traceback__)+'\n')


def get_new_chapter_no():
    with open(TEMP_FILE, 'r') as r:
        url = r.read().strip()
    m = ncode_pattern.match(url)
    novel = m.group(3)
    chapter = int(m.group(4)) + 1
    try:
        next_chap = scrapper.chap_url.substitute(novel=novel, chapter=chapter)
        raw_file = os.path.join(config.root_path,
                                f'data/{novel}_{chapter}-jp.txt')
        scrapper.save_chapter(novel, chapter, filename=raw_file)
    except scrapper.NoChapterException:
        return None, None
    with open(TEMP_FILE, 'w') as w:
        w.write(next_chap)

    # the chapter number for arc7 starts from 503
    if chapter < 516:
        return chapter - 502, next_chap
    # EX chapter on 516, that's why
    return chapter - 503, next_chap


async def send_chapter_alert(chap_num, chap_url):
    servers = filter(lambda g: g.id in inform_guilds, client.guilds)
    for g in servers:
        channel = filter(lambda c: c.name in ['general'], g.channels)
        for c in channel:
            await c.send("@newChapterAlert chapter-" +
                         f"{chap_num} has been released. ")
            code = "/".join(chap_url.split("/")[-3:-1])
            await c.send(f"use command `b! mtl {code}` to get the MTL.")
            print(f'msg sent to:{c.name} of {g.name}')

            
async def check_new_chapter():
    await client.wait_until_ready()
    while True:
        try:
            chap, url = get_new_chapter_no()
            if chap:
                await send_chapter_alert(chap, url)
            await asyncio.sleep(120)    # checks every 2 minutes
        except KeyboardInterrupt:
            break

if __name__ == '__main__':
    client.loop.create_task(check_new_chapter())
    client.run(token)
