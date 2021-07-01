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


# I'm adding userinput as a CLI directly in this command, so never
# ever give permission to use this command to other people as they can
# crash your server or do worse. :tehe:
async def cmd_ocr(message, args):
    """Performs OCR on the uploaded image

Usage: ocr [-v] [args]

    -v  : Optional argument passed for vertical OCR
    args: Commandline arguments for tesseract. for more info look into `man tesseract`.
    """
    remove_spaces = False
    if args.strip() == '-v':
        options = ' -l jpn_vert'
        remove_spaces = True
    elif args.strip() == '':
        options = ' -l jpn'
    elif re.match(r'[a-z+_ -]+' ,args):
        options = args
        if 'jpn_vert' in args:
            remove_spaces = True
    else:
        await message.reply("Invalid options.")
        return
    if len(message.attachments) == 0:
        process = subprocess.Popen(
            f'tesseract ' + options,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = process.communicate()
        await message.reply(out.decode())
        return
    for attch in message.attachments:
        if 'image' not in attch.content_type:
            await message.reply("Please send an image text file")
            return
        temp_img_file = f"/tmp/{attch.filename}"
        temp_ocr_file = f"/tmp/ocr-{attch.filename}"
        with open(temp_img_file, "wb") as w:
            r = requests.get(attch.url)
            w.write(r.content)

        print(f'tesseract {temp_img_file} {temp_ocr_file} ' + options)
        process = subprocess.Popen(
            f'tesseract {temp_img_file} {temp_ocr_file} ' + options,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = process.communicate()
        os.remove(temp_img_file)

        temp_ocr_file += ".txt"
        with open(temp_ocr_file, "r") as r:
            content = r.read()
        if remove_spaces:
            content = content.replace(" ", "")
        if len(content.strip()) == 0:
            await message.reply("Sorry I couldn't extract any text.")
        elif len(content) < 100:
            await message.reply(content)
        else:
            with open(temp_ocr_file, "w") as w:
                w.write(content)
            await utilities.reply_file(message, filename=temp_ocr_file,
                                       content="Here you go.")
        os.remove(temp_ocr_file)


