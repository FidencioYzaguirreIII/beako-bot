"""Commands for discord bot in privileged servers, each command will have a line passed to it
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
