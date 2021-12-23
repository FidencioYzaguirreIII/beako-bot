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
from privilege_commands import *

def new_chapter(chapter, sections):
    with open(config.status_file, 'r') as r:
        status = json.load(r)
    chapter = str(chapter)
    if chapter in status:
        return 'Chapter already in database'
    status[chapter] = dict(
        status='Queued',
        assignments=dict(
            Translation={(i+1): {} for i in range(sections)},
            Japanese={(i+1): {} for i in range(sections)},
            Proofreading={(i+1): {} for i in range(sections)},
        )
    )
    with open(config.status_file, 'w') as w:
        json.dump(status, w, indent=2)
    return 'Chapter Added to the database'


def assign_to(name, chapter, section, part, assist=False):
    with open(config.status_file, 'r') as r:
        status = json.load(r)
    try:
        chap = status[chapter]
    except KeyError:
        return f'Chapter-{chapter} is not available.'
    if chap['status'] == 'Completed':
        return f'Chapter-{chapter} is already completed.'
    else:
        chap['status'] = 'In Progress'
        sec = chap['assignments'][part][section]
        try:
            msg = f'Already assigned to :{sec["assignee"]}'
            if not assist:
                return msg
            sec['assignee'] += f'; {name}'
            msg += f'Adding {name} for assist.'
        except KeyError:
            sec['assignee'] = name
            sec['progress'] = 'Assigned'
            msg = f'{part} for Chapter-{chapter}, Section-{section}' +\
                f' assigned to {name}.'
    with open(config.status_file, 'w') as w:
        json.dump(status, w, indent=2)
    return msg


def mark_completed(chapter, section=None, part=None):
    with open(config.status_file, 'r') as r:
        status = json.load(r)
    chap = status[chapter]
    if section is None and part is None:
        if chap['status'] == 'Completed':
            msg = f'Chapter-{chapter} was already marked as completed.'
        else:
            chap['status'] = 'Completed'
            msg = f'Chapter-{chapter} marked as completed.'
    else:
        try:
            chap['assignments'][part][section]['progress'] = 'Completed'
            msg = f'{part}: Chapter-{chapter}, Section-{section} marked as completed.'
        except KeyError:
            return 'Given chapter or section not found.'
    with open(config.status_file, 'w') as w:
        json.dump(status, w, indent=2)
    return msg


def get_work(work_str):
    if work_str is None:
        return ''
    for possible_work in ["Translation", "Japanese", "Proofreading"]:
        if possible_work.lower().startswith(work_str.lower()):
            return possible_work
    return ''


async def cmd_assign(message, args, assist=False):
    """Assign given chapter and section to someone or yourself.
Usage: assign <cs-string> <work> <person>
Arguments:
    <cs-string> : chapter & section in c#s# format.
    <work>      : Translation, Proofreading, or Japanese. You can also use short version (t, p & j)
    <person>    : The person it is assigned to, if not mentioned the one who sent the message will be assigned.
the section and chapter number can contain range like 1-5 for from 1 to 5, or 3,5 for 3 and 5.
e.g. assign c9s1 t void; assign c8s3 t; etc.
    """
    m = re.match(r'([cs0-9,-]+) ([A-Za-z]+) ?[@]?([\w]+)?', args)
    if not m:
        await message.reply('Incorrect formatting for command.')
        return
    work = get_work(m.group(2))
    if work == '':
        await message.reply('Incorrect formatting for command.')
        return
    if not m.group(3):
        assignee = str(message.author)
    else:
        assignee = m.group(3)
    chap, sec = get_chapter_section(m.group(1))
    if chap is None or sec is None:
        await message.reply('Incorrect formatting for command.')
        return
    for c in chap:
        for s in sec:
            await message.reply(assign_to(assignee, c, s, work, assist))


async def cmd_assist(message, args):
    """Same as assign but adds the person as assist to already available one.
Usage: assist <cs-string> <work> <person>
Look help assign for other information.
    """
    await cmd_assign(message, args, assist=True)


async def cmd_completed(message, args):
    """Mark given chapter and section completed.
Usage: completed <cs-string> <work>
Arguments:
    <cs-string> : chapter & section in c#s# format.
    <work>      : Translation, Proofreading, or Japanese. You can also use short version (t, p & j)
the section and chapter number can contain range like 1-5 for from 1 to 5, or 3,5 for 3 and 5.
e.g. completed c9s1 t; completed c8s3 t; etc.
    """
    m = re.match(r'([cs0-9,-]+) ?([A-Za-z]+)?', args)
    if not m:
        await message.reply('Incorrect formatting for command.')
        return
    work = get_work(m.group(2))
    chap, sec = get_chapter_section(m.group(1))
    if chap is None:
        await message.reply('Incorrect formatting for command.')
        return
    if sec is None:
        for c in chap:
            await message.reply(mark_completed(c))
    for c in chap:
        for s in sec:
            await message.reply(mark_completed(c, s, work))


async def cmd_add(message, args):
    """Adds the chapter to the database.
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
