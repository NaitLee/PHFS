#!/usr/bin/python3

import urllib
from classesLib import DictAsObject

def object_from_dict(d: dict):
    """ Get a `DictAsObject` from a normal `dict`
    """
    n = DictAsObject()
    for i in d:
        n[i] = d[i]
    return n

def replace_str(str0: str, str1: str, str2: str):
    """ A faster string replacer for once replacing.  
        `str0`: Source string  
        `str1`: Original string  
        `str2`: Target string
    """
    results = []
    str1_len = len(str1)
    parsing_len = len(str0) - str1_len + 1
    if parsing_len >= 0 and str1_len > 0:
        i = 0
        while i <= parsing_len:
            if i >= 0:
                sliced = str0[i:i + str1_len]
                if sliced == str1:
                    results.append(str2)
                    i += str1_len
                    # Remove this break if want to replace all, but slower than native str.replace()
                    break
                results.append(str0[i])
            i += 1
        results.append(str0[i:])
        return ''.join(results)
    return str0

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
def concat_list(*lists):
    new_list = []
    for i in lists:
        for j in i:
            new_list.append(j)
    return new_list

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
