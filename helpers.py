#!/usr/bin/python3

import urllib

def parse_ini(c: str):
    """ Parse an ini content, returns a dict """
    d = {}
    for i in c.split('\n'):
        if '=' not in i or len(i) == 0:
            continue
        j = i.split('=')
        d[j[0]] = j[1]
    return d

def read_ini(f: str):
    """ Read an .ini file, returns a dict """
    f = open(f, 'r', encoding='utf-8')
    c = f.read()
    f.close()
    return parse_ini(c)

units = ['','K','M','G','T']
for c in range(97, 123):    # aa-zz
    units.append(chr(c)+chr(c))

def smartsize(b: int):
    """ Get a number with unit, 1024 = 1 K etc. """
    i = 0
    j = 0
    while j <= b:
        i += 1
        j = 1 << (i * 10)
    i -= 1
    n = b / (1 << (i * 10))
    return str(round(n, 1)) + ' ' + units[i]

def wildcard2re(e: str):
    return e.replace('*', '.*').replace('?', '.?').replace(';', '|')

def concat_dict(*dicts):
    new_dict = {}
    for i in dicts:
        for j in i:
            new_dict[j] = i[j]
    return new_dict

def purify(s: str):
    """ uriencode input string, change \\ to / """
    return urllib.parse.quote(s).replace('%5C', '/').replace('%2F', '/')  # %5C \ %2F / -> /
def recover(s: str):
    """ uridecode input string """
    return urllib.parse.unquote(s)

def replacepairs(s: str, *args):
    for i in args:
        s = s.replace(i[0], i[1])
    return s

def trimiterable(i):
    """ Maps an iterable, trims strings inside """
    return list(map(lambda s: s.strip(), i))
