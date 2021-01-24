import requests
from bs4 import BeautifulSoup
import re
from string import Template

chap_url  = Template("http://ncode.syosetu.com/${novel}/${chapter}/")
headers = {
'User-Agent' : "Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0"
}

class NoChapterException(Exception):
    pass

def get_soup(url):
    print(f'connecting...{url}')
    r = requests.get(url, headers = headers)
    if r.status_code == 404:
        print('404 Error.')
        raise NoChapterException
    print(':Connected:')
    return BeautifulSoup(r.text,'html.parser')


def get_chapter(novel, chap_no):
    soup = get_soup(chap_url.substitute(novel=novel, chapter=chap_no))
    entry = soup.find('div',{'id':'novel_contents'})
    chapname = entry.find('p',{'class':'novel_subtitle'})
    content = entry.find('div',{'id':'novel_honbun'})

    chaptitle = chapname.text
    contents = content.text

    print(f'Completed::{chap_no}-{chaptitle}')
    return (chaptitle,contents)


def save_chapter(novel, chap_no, filename=None):
    chaptitle, contents = get_chapter(novel, chap_no)
    if filename is None:
        filename = f'./data/{novel}_{chap_no}.txt'
    with open(filename, 'w') as w:
        w.write(f'* {chaptitle}\n')
        w.write(contents)
    return filename

