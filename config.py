import os
import re

from dotenv import load_dotenv


root_path = os.path.dirname(__file__)
load_dotenv(os.path.join(root_path, ".env"))

ncode_pattern = re.compile(r'(https?://)?(ncode.syosetu.com/?)?([a-z0-9]+)/([0-9]+)/?')
bot_pattern = re.compile(r"b! +([a-zA-Z0-9-]+) ?(.*)")
chapter_pattern = re.compile(r'([a-z0-9]+) ?([0-9]+)')


log_file = os.path.join(root_path, '.bot.log')
temp_file = os.path.join(root_path, '.temp_file')
status_file = os.path.join(root_path, 'tables/status.json')
kanji_exe = os.path.join(root_path, 'kanji')

#inform_guilds = [int(os.getenv('TEST_GUILD_ID'))]  # my test server
inform_guilds = [int(os.getenv('HERETIC_GUILD_ID')),
                 int(os.getenv('HERETIC_PUBLIC_GUILD_ID'))]  # Heretics
admin_guilds = [int(os.getenv('HERETIC_GUILD_ID'))]  # Heretics
privileged_guilds = [int(os.getenv('HERETIC_PUBLIC_GUILD_ID'))]  # Heretics public


novels = {'rezero': 'n2267be'}

if not os.path.isdir(os.path.join(root_path, 'data')):
    os.mkdir(os.path.join(root_path, 'data'))
if not os.path.isdir(os.path.join(root_path, 'tables')):
    os.mkdir(os.path.join(root_path, 'tables'))

token = os.getenv('DISCORD_TOKEN')
