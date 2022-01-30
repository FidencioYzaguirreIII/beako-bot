"""Commands for discord bot in admin servers, each command will have a line passed to it
the message it got."""

import sys
import os
import inspect
import json
import re
import random
from string import Template
import urllib.request
from urllib.parse import urlparse
import subprocess

import config
import requests
import utilities
import scrapper
import deepl

# adding all the commands to this as well
from commands import *
from privilege_commands import *L

async def cmd_add(message, args):
    """s the chapter to the database.
Usage: add <chapter> <sections>
Arguments:
    <chapter> : chapter number.
    <section> : number of sections in this chapter.
"""
    m = re.match(r'([0-9]+) ([0-9]+)', args)
    if not m:
        await message.reply("Incorrect formatting for the command.")
    try:
        chapter = int(m.group(1))
        section = int(m.group(2))
        await message.reply(new_chapter(chapter, section))
    except ValueError:
        await message.reply('Use numbers for chapters and sections')


async def cmd_deepl(message, args):
    """Uses deepl website to translate a plain text file.

Usage: deepl <attachment>

    <attachment>: A plain text file in utf-8 encoding.
"""
    await message.reply("it might take a while, I'll ping you when I'm done.")
    for attch in message.attachments:
        if 'text/plain' not in attch.content_type:
            await message.reply("Please send a plain text file")
            return
        temp_og_file = f"/tmp/{attch.filename}"
        temp_tl_file = f"/tmp/tl-{attch.filename}"
        with open(temp_og_file, "w") as w:
            r = requests.get(attch.url)
            r.encoding = 'utf-8'
            w.write(r.text)

        # Implement it once it's sure every process will close firefox after done.

        # while not deepl.web:
        #     # waits if another deepl translation is going on
        #     await asyncio.sleep(10)

        await deepl.init_web()
        await deepl.translate(temp_og_file, temp_tl_file)
        await deepl.close_web()

        await utilities.reply_file(message, temp_tl_file, "Here you go")
        # remove the followings during debug
        os.remove(temp_og_file)
        os.remove(temp_tl_file)


async def cmd_check(message, args):
    """checks if the new episode is out or not.

Usage: check

No arguments.
    """
    with open(config.temp_file, 'r') as r:
        url = r.read().strip()
    m = config.ncode_pattern.match(url)
    novel = m.group(3)
    chapter = int(m.group(4)) + 1
    try:
        next_chap = scrapper.chap_url.substitute(novel=novel, chapter=chapter)
        raw_file = os.path.join(config.root_path, f'data/{novel}_{chapter}-jp.txt')
        scrapper.save_chapter(novel, chapter, filename=raw_file)
    except scrapper.NoChapterException:
        await message.reply("Sorry there are no new chapters in the website.")
        return

    await message.reply(
        "<@&846779183303491625> The new chapter is out" +
        ", you can check it in the" +
        f" link:\n{next_chap}\n use `b! mtl {novel}/{chapter}`" +
        " command if you want mtl for the new chapter")
    with open(config.temp_file, 'w') as w:
        w.write(next_chap)



# UTILITIES AND OTHER FUNCTIONS FROM HERE ONWARDS

# this help overwrites the one from commands.py
async def cmd_help(message, args):
    """The help message with available commands for the bot.
Usage: help <topic>
Arguments:
    <topic> : Can be any command or non for brief help of all commands.
e.g: help help; help add; etc.
"""
    if args.strip() == '':
        msg = 'This bot can be used to manage/view the assignments of the works. and many other functions.\n'
        msg += 'Available commands:\n'
        commands = filter(lambda x: inspect.isfunction(x[1]) and
                          x[0].startswith('cmd_'),
                          inspect.getmembers(sys.modules[__name__]))
        for name, func in commands:
            short_help = func.__doc__.split('\n')[0]
            msg += f'{name[4:]} - {short_help}\n'
    else:
        try:
            func = getattr(sys.modules[__name__], f'cmd_{args}')
            msg = func.__doc__
        except AttributeError:
            msg = 'Requested command is not available'
    await message.reply(msg)


async def cmd_ip(message, args):
    """Gives the IP address of the bot to ssh into it.
Usage: ip
"""
    soup = scrapper.get_soup("http://checkip.dyndns.org/")
    ip = soup.find('body').text
    await message.reply(ip)


async def cmd_dark(message, args):
    """gives a link to the dark website curresponsing to the heretics website link.
    """
    soup = scrapper.get_soup("http://checkip.dyndns.org/")
    ip = soup.find('body').text.split(" ")[-1]
    path = urlparse(args).path
    await message.reply(f"Visit: http://{ip}:5006{path}")


