import os
import discord
import scrapper
import deepl
import config

novels = {'rezero': 'n2267be'}


def parse_novel(title, chapter):
    title = novels.get(title, title)
    return title, chapter


async def send_file(channel, filename):
    f = open(filename, 'rb')
    df = discord.File(fp=f)
    await channel.send(file=df)
    f.close()


async def from_ncode(novel, chapter, channel, filename=None, upload_file=True):
    if filename is None:
        filename = os.path.join(config.root_path,
                                f'data/{novel}_{chapter}-jp.txt')
    if os.path.isfile(filename):
        if upload_file:
            await send_file(channel, filename)
        return filename
    url = scrapper.chap_url.substitute(novel=novel, chapter=chapter)
    await channel.send(f'Just a sec, I\'ll go visit ncode website.')
    try:
        filename = scrapper.save_chapter(novel, chapter, filename=filename)
        if upload_file:
            await send_file(channel, filename)
        return filename
    except scrapper.NoChapterException:
        await channel.send('The requested chapter is not available.')
        return None
    except Exception as e:
        await channel.send('Something went wrong, message thevoidzero.')
        raise e


async def mtl_ncode(novel, chapter, channel, outfile=None):
    rawfile = await from_ncode(novel, chapter, channel,
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
        await channel.send("The translation might take a while, I'll upload when it's finished.")
        if deepl.web is None:
            await deepl.init_web()
        await deepl.translate(rawfile, outfile)
    await send_file(channel, outfile)
