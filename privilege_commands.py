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


@utilities.restrict_roles(config.mtl_roles)
async def cmd_mtl(message, args):
    """Downloads the chapter and uploads a mtl from ncode website.
Usage: mtl <ncode-link>
    """
    link = config.ncode_pattern.match(args)
    if not link:
        ch = config.chapter_pattern.match(args)
        if not ch:
            await message.reply("Send ncode link to get text.")
            return
        novel, chapter = utilities.parse_novel(ch.group(1), ch.group(2))
        await utilities.mtl_ncode(novel, chapter, message)
    else:
        await utilities.mtl_ncode(link.group(3),
                                  link.group(4),
                                  message)

@utilities.restrict_roles(config.ocr_roles)
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


@utilities.restrict_roles(config.ocr_roles)
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


@utilities.restrict_roles(config.mtl_roles)
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
