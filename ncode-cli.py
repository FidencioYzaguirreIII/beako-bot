import os
import re
import asyncio
import subprocess
import discord
import scrapper
import deepl

from shutil import copyfile
from dotenv import load_dotenv

bot_pattern = re.compile(r"b! +([a-zA-Z0-9-]+) ?(.*)")
ncode_pattern = re.compile(
    r'(https?://)?(ncode.syosetu.com/?)?([a-z0-9]+)/([0-9]+)/?')
chapter_pattern = re.compile(r'([a-z0-9]+) ?([0-9]+)')
root_path = '/home/gaurav/python/discord/'
temp_file = os.path.join(root_path, '.temp_file')

novels = {'rezero': 'n2267be'}
# inform_guilds = [802505736218214420]  # my test server
inform_guilds = [772947291606614026]  # Heretics


async def send_file(channel, filename, msg=None):
    f = open(filename, 'rb')
    df = discord.File(fp=f, filename=filename.split('/')[-1])
    await channel.send(content=msg, file=df)
    f.close()


def send_message(msg=None, filename=None):
    load_dotenv(dotenv_path=os.path.join(root_path, '.env'))
    token = os.getenv('DISCORD_TOKEN')

    asyncio.set_event_loop(asyncio.new_event_loop())
    client = discord.Client()

    async def send_message_task():
        await client.wait_until_ready()
        print(f'{client.user} has connected to Discord.')
        servers = filter(lambda g: g.id in inform_guilds, client.guilds)
        for g in servers:
            channel = filter(lambda c: c.name in ['general'], g.channels)
            for c in channel:
                if filename:
                    await send_file(c, filename, msg=msg)
                    print(f'file sent to:{c.name} of {g.name}')
                else:
                    await c.send(msg)
                    print(f'msg sent to:{c.name} of {g.name}')
        await asyncio.sleep(2)
        await client.logout()

    client.loop.create_task(send_message_task())
    try:
        client.run(token)
    except RuntimeError:
        return


def check_revisions(novel, chapters):
    novel = 'n2267be'
    chapter = '512'
    for chapter in chapters:
        new_file = f'/tmp/{novel}_{chapter}-jp.txt'
        old_file = f'./data/{novel}_{chapter}-jp.txt'
        scrapper.save_chapter(novel, chapter, filename=new_file)
        process = subprocess.Popen(f'git diff {old_file} {new_file}',
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()
        diff = out.decode()
        if (len(diff.split('\n'))) < 5:
            continue
        copyfile(new_file, old_file)
        w = open("/tmp/ch-512.diff","w")
        w.write(diff)
        w.close()


def check_new_episode():
    with open(temp_file, 'r') as r:
        url = r.read().strip()
    m = ncode_pattern.match(url)
    novel = m.group(3)
    chapter = int(m.group(4)) + 1
    try:
        next_chap = scrapper.chap_url.substitute(novel=novel, chapter=chapter)
        raw_file = os.path.join(root_path, f'data/{novel}_{chapter}-jp.txt')
        scrapper.save_chapter(novel, chapter, filename=raw_file)
        outfile = os.path.join(root_path, f'data/{novel}_{chapter}-en.txt')
        if not os.path.exists(outfile):
            asyncio.run(deepl.init_web())
            asyncio.run(deepl.translate(raw_file, outfile))
            asyncio.run(deepl.close_web())
    except scrapper.NoChapterException:
        return None, None
    with open(temp_file, 'w') as w:
        w.write(next_chap)
    return outfile, chapter


if __name__ == '__main__':
    while True:
        doc, chap = check_new_episode()
        if not doc:
            break
        send_message("@everyone New chapter has been released.\n" +
                     f"Here's the MTL for Rezero Arc7 Chapter-{chap-502}.",
                     filename=doc)
