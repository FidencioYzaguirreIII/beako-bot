import os
import re
import time
import asyncio
import json

import selenium
from selenium import webdriver
from dotenv import load_dotenv

MAX_DELAY_SEC = 120
MIN_DELAY_SEC = 5

web = None

root_path = '/home/gaurav/python/discord/'
replacements = os.path.join(root_path, 'replacements.json')

load_dotenv(dotenv_path=os.path.join(root_path, '.env'))


async def close_web():
    global web
    if web:
        web.close()
        web = None


async def init_web():
    global web
    opt = webdriver.FirefoxOptions()
    opt.set_headless()
    prof = webdriver.FirefoxProfile()
    prof.set_preference("dom.webdriver.enabled", False)
    prof.set_preference('useAutomationExtension', False)
    prof.update_preferences()

    print(f'Opening web browser.')
    web = webdriver.Firefox(
        firefox_profile=prof,
        firefox_options=opt,
        desired_capabilities=webdriver.DesiredCapabilities.FIREFOX)

    print('Loading deepl website.')
    web.get('https://www.deepl.com/translator')
    await asyncio.sleep(10)
    try:
        cookieBtn = web.find_element_by_class_name(
            'dl_cookieBanner--buttonClose')
        cookieBtn.click()
    except selenium.common.exceptions.NoSuchElementException:
        pass
    return web


async def login():
    # not used for now.
    global web
    print('Logging into the deepl website.')
    login = web.find_element_by_class_name('dl_header_menu_v2__login_button')
    login.click()
    web.find_element_by_name("login-email").send_keys(os.getenv('DEEPL_EMAIL'))
    web.find_element_by_name("login-password").send_keys(os.getenv('DEEPL_PASS'))
    login = web.find_element_by_class_name(
        'dl_menu__login__form__submit').click()
    await asyncio.sleep(5)  # check logged in later
    return


async def process_text(text):
    inputarea = web.find_element_by_class_name('lmt__source_textarea')
    outputarea = web.find_element_by_id('target-dummydiv')

    inputarea.clear()
    inputarea.send_keys(text)
    await asyncio.sleep(MIN_DELAY_SEC)
    for i in range(MAX_DELAY_SEC - MIN_DELAY_SEC):
        await asyncio.sleep(1)
        translated = outputarea.get_attribute('innerHTML')
        if translated.count('[...]') > 5:
            continue
        if translated and outputarea.is_enabled() and inputarea.is_enabled():
            break
    return translated


def replace_words(text):
    if replacements == '' or not os.path.isfile(replacements):
        rep = dict()
    else:
        with open(replacements, 'r') as r:
            rep = json.load(r)

    text = re.sub(r'\n\n+', '\n\n', text)
    for k, v in rep.items():
        print(f'REPLACE: {k}-->{v}')
        text = text.replace(k, v)
    return text


async def translate(input_file, output_file, paid=False):
    with open(input_file, 'r') as r:
        filecontent = replace_words(r.read())
    if paid:
        LIMIT = 5000
    else:
        LIMIT = 3800
    lines = filecontent.splitlines()
    content = ''
    tl_doc = ''
    print(f'TRANSLATION: {len(lines)} lines file.')
    for i, line in enumerate(lines, start=1):
        if len(content) > LIMIT:
            tl_doc += await process_text(content) + '\n'
            print(f'{i} lines completed...')
            content = ''
        else:
            content += line + '\n'

    tl_doc += await process_text(content)
    tl_doc = re.sub(r'\n+ *', '\n\n', tl_doc)
    with open(output_file, 'w') as w:
        w.write(tl_doc)
    print(f'Written to {output_file}')
