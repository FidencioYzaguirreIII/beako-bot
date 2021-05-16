import os
import re
import discord
import scrapper
import utilities

from dotenv import load_dotenv

bot_pattern = re.compile(r"b! +([a-zA-Z0-9-]+) ?(.*)")
ncode_pattern = re.compile(r'(https?://)?(ncode.syosetu.com/?)?([a-z0-9]+)/([0-9]+)/?')
chapter_pattern = re.compile(r'([a-z0-9]+) ?([0-9]+)')

novels = {'rezero': 'n2267be'}

if not os.path.isdir('./data'):
    os.mkdir('data')
if not os.path.isdir('./rezero'):
    os.mkdir('rezero')

load_dotenv()
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
    m = ncode_pattern.match(message.content.lower())
    if m:
        await utilities.from_ncode(m.group(3), m.group(4), message.channel)
        return
    m = bot_pattern.match(message.content.lower())
    if not m:
        return
    cmd = m.group(1)
    args = m.group(2)
    if cmd == 'help':
        await utilities.help_message(message.channel)
    elif cmd == 'ncode':
        link = ncode_pattern.match(args)
        if not link:
            ch = chapter_pattern.match(args)
            if not ch:
                await message.channel.send("Send ncode link to get text.")
                return
            novel, chapter = utilities.parse_novel(ch.group(1), ch.group(2))
            await utilities.from_ncode(novel, chapter, message)
        else:
            await utilities.from_ncode(link.group(3), link.group(4), message)
    elif cmd == 'deepl':
        if args:
            link = ncode_pattern.match(args)
            if not link:
                ch = chapter_pattern.match(args)
                if not ch:
                    await message.channel.send("Send ncode link to get text.")
                    return
                novel, chapter = utilities.parse_novel(ch.group(1), ch.group(2))
                await utilities.mtl_ncode(novel, chapter, message)
            else:
                await utilities.mtl_ncode(link.group(3), link.group(4), message)
        else:
            files = os.listdir('./data')
            chapters = filter(lambda l: re.match(r'[a-z0-9]+_[0-9]+-en.txt',l), files)
            chaps = '\n'.join(chapters)
            await message.channel.send(f'Available files: \n{chaps}')
    elif cmd == 'arc7jp':
        chap = int(args) + 502
        await utilities.from_ncode(novels['rezero'], chap,
                         message, filename=f'./rezero/arc7-ch{args}-jp.txt')
    elif cmd == 'arc7en':
        if args:
            if args.isnumeric():
                filename = f'./rezero/arc7-ch{args}-en.txt'
            else:
                filename = args
            if os.path.isfile(filename):
                await utilities.reply_file(message, filename)
            else:
                chap = int(args) + 502
                await utilities.mtl_ncode(novels['rezero'], chap,
                         message, outfile=filename)
        else:
            files = os.listdir('./rezero')
            chapters = filter(lambda l: re.match(r'arc7-ch[0-9]+-en.txt',l), files)
            chaps = '\n'.join(chapters)
            await message.channel.send(f'Available files: \n{chaps}')
    else:
        await utilities.chat_bot(message)


# @client.event
# async def on_error(*args):
#     print('Error')
#     print(args)
    # await ctx.send(f'Some error occured, contant thevoidzero.')


if __name__ == '__main__':
    client.run(token)
