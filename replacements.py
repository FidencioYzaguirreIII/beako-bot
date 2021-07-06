import re
import sys
import json
import os

from enum import Flag
from collections import namedtuple


class Names(Flag):
    NONE = 0
    FULL_NAME = 1
    FIRST_NAME = 2
    FULL_AND_FIRST = 3
    LAST_NAME = 4
    FULL_AND_LAST = 5 
    FIRST_AND_LAST = 6
    ALL_NAMES = 7


Character = namedtuple('Character', 'last_jp_name first_jp_name en_name')


VERBOSE = True
SINGLE_KANJI_FILTER=True
text = ''
rep = dict()
total_replacements = 0


def out_filename(in_file):
    p, e = os.path.splitext(in_file)
    return f'{p}-rep{e}'


def replace_single_word(word, replacement):
    global text, total_replacements
    n = text.count(word)
    if n == 0:
        return 0
    text = text.replace(word, replacement)
    total_replacements += n
    return n


def loop_names(character,
               replace=Names.FULL_NAME,
               honorific=Names.ALL_NAMES):
    if Names.FULL_NAME in replace:
        yield (character.en_name,
               f'{character.last_jp_name}・{character.first_jp_name}',
               Names.FULL_NAME in honorific)
    if Names.FIRST_NAME in replace:
        yield (character.en_name.split()[-1],
               f'{character.first_jp_name}',
               Names.FIRST_NAME in honorific)
    if Names.LAST_NAME in replace:
        yield (character.en_name.split()[0],
               f'{character.last_jp_name}',
               Names.LAST_NAME in honorific)


def replace_name(character,
                 replace=Names.FULL_NAME,
                 no_honorific=Names.ALL_NAMES):
    data = dict()
    for nen, njp, no_honor in loop_names(character, replace, no_honorific):
        data[nen] = dict()
        for hon, hon_en in rep['honorifics'].items():
            data[nen][hon_en] = replace_single_word(
                f'{njp}{hon}',
                f'{nen}-{hon_en}'
            )
        if no_honor:
            if len(njp) > 1 or not SINGLE_KANJI_FILTER:
                data[nen][''] = replace_single_word(njp, nen)
    if not VERBOSE:
        return
    for k,v in data.items():
        total = sum(v.values())
        if total == 0:
            continue
        
        print(f'    {k} :{total} (', end='')
        print(", ".join(map(lambda x: f'{x}-{v[x]}',
                            filter(lambda x: v[x]>0, v))), end=')\n')


def replace(input_text, replacements):
    global text, rep
    text = input_text
    rep = replacements
    
    rules = [
        # title, json_key, is_name, replace_name, no_honorifics
        ('Special', 'specials', False),
        ('Basic', 'basic', False),
        ('Names', 'names', True,
         Names.ALL_NAMES, Names.ALL_NAMES),
        ('Single Names', 'single-names', True,
         Names.LAST_NAME, Names.LAST_NAME),
        ('Remaining Names', 'full-names', True,
         Names.ALL_NAMES, Names.FULL_NAME),
        ('Name like', 'name-like', True, Names.LAST_NAME, Names.NONE),
        ('Final', 'final', False)
    ]

    for rule in rules:
        prev_count = total_replacements
        if VERBOSE:
            print(f'* {rule[0]} Replacements:')
        if rule[2]:
            for k, v in rep[rule[1]].items():
                if not isinstance(v, list):
                    v = [v, '']
                elif len(v) == 1:
                    v.append('')
                char = Character(*v, k)
                replace_name(char, rule[3], rule[4])
        else:
            for k, v in rep[rule[1]].items():
                n = replace_single_word(k, v)
                if n > 0:
                    print(f'    {k} → {v}:{n}')
        print(f'  SubTotal: {total_replacements-prev_count}')
    return text


def main(input_file, rep_file):
    global total_replacements
    with open(input_file,'r') as r:
        text = r.read()

    with open(rep_file,'r') as r:
        rep = json.load(r)

    text = replace(text, rep)
    print(f'Total Replacements: {total_replacements}')

    out_file = out_filename(input_file)
    with open(out_file, 'w') as w:
        w.write(text)

    print(f'Output written to: {out_file}')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f'Usage: {sys.argv[0]} input_file replacement_json')
        exit(0)
    main(sys.argv[1], sys.argv[2])
