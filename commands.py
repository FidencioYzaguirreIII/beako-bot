"""Commands for discord bot in public servers, each command will have a line passed to it
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
from shutil import copyfile

import config
import requests
import utilities
import scrapper
import deepl


if not os.path.isfile(config.status_file):
    with open(config.status_file, 'w') as w:
        w.write('{}')


def extract_range(range_str):
    if range_str is None or range_str.strip() == '':
        return 'Empty chapter or section'
    ranges = range_str.split(',')
    try:
        for r in ranges:
            if r.strip() == '':
                continue
            if '-' in r:
                rng = r.split('-')
                if len(rng) > 2:
                    return 'Incorrect formatting, use valid range'
                    raise SystemExit
                yield from map(str, range(int(rng[0]), int(rng[1]) + 1))
            else:
                yield str(r)
    except ValueError:
        return 'Incorrect formatting: use integers for chapters and sections'


def get_chapter_section(chap_sec_str):
    m = re.match(r'c?([0-9-,]+)s?([0-9-,]+)?', chap_sec_str)
    if not m:
        return None, None
    elif not m.group(2):
        return extract_range(m.group(1)), None
    else:
        return extract_range(m.group(1)), extract_range(m.group(2))
        

def get_status(chapter=None):
    with open(config.status_file, 'r') as r:
        status = json.load(r)
    if len(status) == 0:
        return 'Status not Available'
    else:
        status_string = ''
    if chapter is not None:
        if chapter not in status:
            return f'No Status for requested chapter: {chapter}'
        status = {chapter: status[chapter]}
    for chap, stat in status.items():
        status_string += f'\nChapter-{chap}: {stat["status"]}'
        for work, data in stat["assignments"].items():
            status_string += f'\n  {work}:'
            for sec, status in data.items():
                status_string += f'\n    Section-{sec}: '
                try:
                    status_string += f'{status["progress"]} ' +\
                        f'({status["assignee"]}); '
                except KeyError:
                    status_string += '----'
    return status_string


def extract_range(range_str):
    if range_str is None or range_str.strip() == '':
        return 'Empty chapter or section'
    ranges = range_str.split(',')
    try:
        for r in ranges:
            if r.strip() == '':
                continue
            if '-' in r:
                rng = r.split('-')
                if len(rng) > 2:
                    return 'Incorrect formatting, use valid range'
                    raise SystemExit
                yield from map(str, range(int(rng[0]), int(rng[1]) + 1))
            else:
                yield str(r)
    except ValueError:
        return 'Incorrect formatting: use integers for chapters and sections'


async def cmd_status(message, args):
    """Current chapters progress and other things.
Usage: status c<chapter>
Arguments:
    <chapter> : chapter number to see the status of. defaults to all,
                use same format as cs string but section information is not used.
"""
    if args.strip() == '':
        msg = get_status()
    else:
        try:
            chap, sec = get_chapter_section(args.strip())
            msg = ""
            for c in chap:
                msg += get_status(c) + '\n'
        except ValueError:
            message.reply('Incorrect Arguments to the command.')
    await message.reply(msg)


async def cmd_hello(message, args):
    """Hello message back to the user.
Usage: hello
No arguments:
You can use this command to check if the bot is online or not.
    """
    await message.reply(f"Hello {message.author.name}")


async def cmd_ncode(message, args):
    """Download the chapter from ncode website
Usage: ncode <ncode-link>
    """
    link = config.ncode_pattern.match(args)
    if not link:
        ch = config.chapter_pattern.match(args)
        if not ch:
            await message.reply("Send ncode link to get text.")
            return
        novel, chapter = utilities.parse_novel(ch.group(1), ch.group(2))
        await utilities.from_ncode(novel, chapter, message)
    else:
        await utilities.from_ncode(link.group(3),
                                   link.group(4),
                                   message)


async def cmd_diff(message, args):
    """Checks if the given chapter had had any revisions since the last check.

Usage: diff <ncode_link>

    <ncode_link>: url of the ncode website to find the chapter on.
    """
    link = config.ncode_pattern.match(args)
    if not link:
        ch = config.chapter_pattern.match(args)
        if not ch:
            await message.reply("Send ncode link to get text.")
            return
        novel, chapter = utilities.parse_novel(ch.group(1), ch.group(2))
    else:
        novel, chapter = utilities.parse_novel(link.group(3), link.group(4))

    new_file = f'/tmp/{novel}_{chapter}-jp.txt'
    old_file = os.path.join(config.root_path, f'data/{novel}_{chapter}-jp.txt')
    if not os.path.exists(old_file):
        await message.reply("Old copy to check for the revisions doesn't exist, sorry.")
        return
    scrapper.save_chapter(novel, chapter, filename=new_file)
    process = subprocess.Popen(f'git diff {old_file} {new_file}',
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = process.communicate()
    diff = out.decode()
    if (len(diff.split('\n'))) < 5:
        await message.reply("No significant changes in this chapter.")
        return
    copyfile(new_file, old_file)
    w = open(f"/tmp/ch-{chapter}.diff","w")
    w.write(diff)
    w.close()
    await utilities.reply_file(message, filename=f"/tmp/ch-{chapter}.diff",
                              content="The changes are in this Diff file.")
    


# UTILITIES AND OTHER FUNCTIONS FROM HERE ONWARDS

async def cmd_help(message, args):
    """The help message with available commands for the bot.
Usage: help <topic>
Arguments:
    <topic> : Can be any command or non for brief help of all commands.
e.g: help help; help add; etc.
"""
    if args.strip() == '':
        msg = 'This bot can be used to manage the assignments of the works.\n'
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


async def cmd_message(message, args):
    """this function is to reply any messages that are not associated with
any commands.
Usage: message <your message>
       OR just <your message that doesn't start with a command.> 
    """
    m = config.ncode_pattern.match(message.content.lower())
    if m:
        await utilities.from_ncode(m.group(3), m.group(4), message)
        return
    await message.reply('Command not recognized, please use' +
                        ' `help` command to get the list.')


async def cmd_joke(message, args):
    """Get random jokes to lighten the channel.
Usage: joke
    """
    headers = {
        "Accept": "Application/json"
    }
    r = requests.get("https://icanhazdadjoke.com/", headers=headers)
    if r.status_code == 200:
        await message.reply(r.json()['joke'])
    else:
        await message.reply(f"Sorry something went wrong. {r.text}")


async def cmd_roast(message, args):
    """roast someone or get roasted by the bot.
Usage: roast <name>
Arguments:
    <name> person you want to roast. Default yourself.
    """
    if args.strip() == '':
        args = message.author.name
    else:
        args = args.strip('@ ')
        if args.lower() == 'otto':
            args = message.author.name
    with open(os.path.join(config.root_path, "./tables/roasts.txt")) as r:
        line = random.choice(r.readlines())
    msg = Template(line).safe_substitute(user=args.capitalize())
    await message.reply(msg)
