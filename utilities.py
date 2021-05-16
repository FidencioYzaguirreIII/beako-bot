import os
import discord
import scrapper
import deepl
import config

novels = {'rezero': 'n2267be'}


def parse_novel(title, chapter):
    title = novels.get(title, title)
    return title, chapter


async def reply_file(message, filename, content=""):
    f = open(filename, 'rb')
    df = discord.File(fp=f)
    await message.reply(file=df, content=content)
    f.close()


async def from_ncode(novel, chapter, message, filename=None, upload_file=True):
    if filename is None:
        filename = os.path.join(config.root_path,
                                f'data/{novel}_{chapter}-jp.txt')
    if os.path.isfile(filename):
        if upload_file:
            await reply_file(message, filename)
        return filename
    url = scrapper.chap_url.substitute(novel=novel, chapter=chapter)
    await message.channel.send(f'Just a sec, I\'ll go visit ncode website.')
    try:
        filename = scrapper.save_chapter(novel, chapter, filename=filename)
        if upload_file:
            await reply_file(message, filename, "Here you go.")
        return filename
    except scrapper.NoChapterException:
        await message.reply('The requested chapter is not available.')
        return None
    except Exception as e:
        await channel.send('Something went wrong, message thevoidzero.')
        raise e


async def mtl_ncode(novel, chapter, message, outfile=None):
    rawfile = await from_ncode(novel, chapter, message,
                               filename=outfile, upload_file=False)
    if not rawfile:
        return
    if outfile:
        f, ext = os.path.splitext(outfile)
        if f.endswith('jp'):
            outfile = f[-2:] + 'en' + ext
        elif not f.endswith('en'):
            outfile = f + 'en' + ext
    else:
        outfile = os.path.join(config.root_path,
                               f'data/{novel}_{chapter}-en.txt')
    if not os.path.isfile(outfile):
        await message.reply("The translation might take a while, I'll upload when it's finished.")
        if deepl.web is None:
            await deepl.init_web()
        await deepl.translate(rawfile, outfile)
    await reply_file(message, outfile, "Here you go.")
