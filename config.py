import os
import re

from dotenv import load_dotenv


root_path = os.path.dirname(__file__)

ncode_pattern = re.compile(r'(https?://)?(ncode.syosetu.com/?)?([a-z0-9]+)/([0-9]+)/?')
bot_pattern = re.compile(r"b! +([a-zA-Z0-9-]+) ?(.*)")
chapter_pattern = re.compile(r'([a-z0-9]+) ?([0-9]+)')


log_file = os.path.join(root_path, '.bot.log')
temp_file = os.path.join(root_path, '.temp_file')
status_file = os.path.join(root_path, 'tables/status.json')


#inform_guilds = [802505736218214420]  # my test server
inform_guilds = [772947291606614026]  # Heretics
admin_guilds = [772947291606614026]  # Heretics


novels = {'rezero': 'n2267be'}

if not os.path.isdir(os.path.join(root_path, 'data')):
    os.mkdir(os.path.join(root_path, 'data'))
if not os.path.isdir(os.path.join(root_path, 'tables')):
    os.mkdir(os.path.join(root_path, 'tables'))

load_dotenv(os.path.join(root_path, ".env"))
token = os.getenv('DISCORD_TOKEN')
