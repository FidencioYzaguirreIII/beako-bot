"""Commands for discord bot, each command will have a line passed to it
the message it got."""

import sys
import os
import inspect
import json
import re

import config

STATUS_FILE = os.path.join(config.root_path, 'tables/status.json')
if not os.path.isfile(STATUS_FILE):
    with open(STATUS_FILE, 'w') as w:
        w.write('{}')


def get_status(chapter=None):
    with open(STATUS_FILE, 'r') as r:
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
        status_string += f'Chapter-{chap}: {stat["status"]}'
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


def new_chapter(chapter, sections):
    with open(STATUS_FILE, 'r') as r:
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
    with open(STATUS_FILE, 'w') as w:
        json.dump(status, w)
    return 'Chapter Added to the database'


def assign_to(name, chapter, section, part, assist=False):
    with open(STATUS_FILE, 'r') as r:
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
    with open(STATUS_FILE, 'w') as w:
        json.dump(status, w)
    return msg


def mark_completed(chapter, section=None, part=None):
    with open(STATUS_FILE, 'r') as r:
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
    with open(STATUS_FILE, 'w') as w:
        json.dump(status, w)
    return msg


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
    m = re.match(r'c([0-9-,]+)s?([0-9-,]+)?', chap_sec_str)
    if not m:
        return None, None
    elif not m.group(2):
        return extract_range(m.group(1)), None
    else:
        return extract_range(m.group(1)), extract_range(m.group(2))


def get_work(work_str):
    if work_str is None:
        return ''
    for possible_work in ["Translation", "Japanese", "Proofreading"]:
        if possible_work.lower().startswith(work_str.lower()):
            return possible_work
    return ''


async def cmd_assign(message, args, assist=False):
    """Assign given chapter and section to someone or yourself.
Usage: completed <cs-string> <work> <person>
Arguments:
    <cs-string> : chapter & section in c#s# format.
    <work>      : Translation, Proofreading, or Japanese. You can also use short version (t, p & j)
    <person>    : The person it is assigned to, if not mentioned the one who sent the message will be assigned.
the section and chapter number can contain range like 1-5 for from 1 to 5, or 3,5 for 3 and 5.
e.g. assign c9s1 t void; assign c8s3 t; etc.
    """
    m = re.match(r'([cs0-9,-]+) ([A-Za-z]+) ?[@]?([\w]+)?', args)
    if not m:
        await message.channel.send('Incorrect formatting for command.')
        return
    work = get_work(m.group(2))
    if work == '':
        await message.channel.send('Incorrect formatting for command.')
        return
    if not m.group(3):
        assignee = str(message.author)
    else:
        assignee = m.group(3)
    chap, sec = get_chapter_section(m.group(1))
    if chap is None or sec is None:
        await message.channel.send('Incorrect formatting for command.')
        return
    for c in chap:
        for s in sec:
            await message.channel.send(assign_to(assignee, c, s, work))


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
        await message.channel.send('Incorrect formatting for command.')
        return
    work = get_work(m.group(2))
    chap, sec = get_chapter_section(m.group(1))
    if chap is None:
        await message.channel.send('Incorrect formatting for command.')
        return
    if sec is None:
        for c in chap:
            await message.channel.send(mark_completed(c))
    for c in chap:
        for s in sec:
            await message.channel.send(mark_completed(c, s, work))


async def cmd_add(message, args):
    """Adds the chapter to the database.
Usage: add <chapter> <sections>
Arguments:
    <chapter> : chapter number.
    <section> : number of sections in this chapter.
"""
    m = re.match(r'([0-9]+) ([0-9]+)', args)
    if not m:
        await message.channel.send("Incorrect formatting for the command.")
    try:
        chapter = int(m.group(1))
        section = int(m.group(2))
        await message.channel.send(new_chapter(chapter, section))
    except ValueError:
        await message.channel.send('Use numbers for chapters and sections')


async def cmd_status(message, args):
    """Current chapters progress and other things.
Usage: status <chapter>
Arguments:
    <chapter> : chapter number to see the status of. defaults to all.
"""
    if args.strip() == '':
        msg = get_status()
    else:
        try:
            msg = get_status(args.strip())
        except ValueError:
            message.channel.send('Incorrect Arguments to the command.')
    await message.channel.send(msg)


async def cmd_hello(message, args):
    """Hello message back to the user.
Usage: hello
No arguments:
You can use this command to check if the bot is online or not.
    """
    await message.channel.send(f"Hello {message.author}")


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
    await message.channel.send(msg)


async def cmd_message(message, args):
    """this function is to reply any messages that are not associated with
any commands.

    """
    await message.channel.send('Command not recognized, please use' +
                               'help command to get the list.')
