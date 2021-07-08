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
    """Performs OCR on the uploaded image, by default assumes Japanese texts in vertical layout.

Usage: ocr [--ops] [args]

possible options (--ops):
    --hz     : Optional argument passed for horizontal OCR
    --vt     : Optional argument passed for vertical OCR
    --line   : expands to option `--psm 7` -> treat the image as a line
    --char   : expands to option `--psm 10` -> treat the image as a char
    --word   : expands to option `--psm 8` -> treat the image as a word
    --sparse : expands to option `--psm 11` -> treat the image as sparse
    --raw    : expands to option `--psm 13` -> treat the image as raw

    args: Commandline arguments for tesseract. for more info look into `man tesseract`.
    """
    if args.strip() == '':
        options = '-l jpn_vert'
    elif re.match(r'[a-z+_ -]+' ,args):
        options = args
        options = options.replace('--hz', '-l jpn')
        options = options.replace('--vt', '-l jpn_vert')
        if '-l ' not in options:
            if '--char' in options:
                options = f'-l jpn {options}'
            else:
                options = f'-l jpn_vert {options}'
        options = options.replace('--line', '--psm 7')
        options = options.replace('--char', '--psm 10')
        options = options.replace('--word', '--psm 8')
        options = options.replace('--sparse', '--psm 11')
        options = options.replace('--raw', '--psm 13')
    else:
        await message.reply("Invalid options.")
        return
    img_len = 0
    for attch in utilities.get_images(message):
        img_len += 1
        if not attch:
            await message.reply("Non-Image attachment detected. Please send an image file," +
                                " or reference an message with an image.")
            continue
        
        temp_img_file = f"/tmp/{attch}"
        temp_ocr_file = f"/tmp/ocr-{attch}"

        print(f'tesseract -c preserve_interword_spaces=1 {options} {temp_img_file} {temp_ocr_file} ')
        process = subprocess.Popen(
            f'tesseract -c preserve_interword_spaces=1 {options} {temp_img_file} {temp_ocr_file} ',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = process.communicate()
        os.remove(temp_img_file)

        temp_ocr_file += ".txt"
        with open(temp_ocr_file, "r") as r:
            content = r.read()
        if len(content.strip()) == 0:
            await message.reply("Sorry I couldn't extract any text.")
        elif len(content) < 200:
            await message.reply(content)
        else:
            with open(temp_ocr_file, "w") as w:
                w.write(content)
            await utilities.reply_file(message, filename=temp_ocr_file,
                                       content="Here you go.")
        os.remove(temp_ocr_file)
    if img_len == 0:
        process = subprocess.Popen(
            'tesseract ' + options,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = process.communicate()
        await message.reply(out.decode())
        return


async def cmd_kanji(message, args):
    """Performs OCR on the uploaded image to find possible Japanese characters.

Usage: kanji

    attachment: image file/files. or reference a message with image.
    """
    img_len = 0
    for attch in utilities.get_images(message):
        img_len += 1
        if not attch:
            await message.reply("Non-Image attachment detected. Please send an image file," +
                                " or reference an message with an image.")
            continue

        temp_img_file = f"/tmp/{attch}"
        kanji_exe = config.kanji_exe

        print(f'{kanji_exe} {temp_img_file}')
        process = subprocess.Popen(
            f'{kanji_exe} {temp_img_file}',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = process.communicate()
        os.remove(temp_img_file)
        if out:
            await message.reply(out.decode())
        else:
            await message.reply("Sorry I couldn't recognize it.")

    if img_len == 0:
        await message.reply("Please attach an image with the command.")


