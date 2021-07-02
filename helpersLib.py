#!/usr/bin/python3

import urllib, os

def sort(l, m, f):
    """ Bubble sort.  
        `l`: the list to be sorted.  
        `m`: the list for comparison.  
        `f`: the function for comparison, takes 2 arguments from `m`, returns a positive or negative number.
    """
    l = list(l)
    m = list(m)
    m_len = len(m)
    for i in range(m_len):
        for j in range(i + 1, m_len):
            if f(m[j], m[i]) <= 0:
                l[j], l[i] = l[i], l[j]
                m[j], m[i] = m[i], m[j]
    return l

def get_dirname(path):
    """ Alternate of os.path.dirname(), which works as we want
    """
    levels = path.split('/')
    if levels[-1] == '':   # is a dir
        return path[0:-1]
    else:
        return '/'.join(levels[:-1])

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
        j = i.split('=', 1)
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

def join_path(path1, path2):
    """ Join two paths, with backslash replaced with slash
        Both `path1` and `path2` are considered non-absolute
    """
    path1 = path1.replace('\\', '/')
    path2 = path2.replace('\\', '/')
    if path1[-1:] != '/':
        path1 = path1 + '/'
    if path2[0:1] == '/':
        path2 = path2[1:]
    return os.path.join(path1, path2)

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

space_chars = ' \n\r\t'
def strip_starting_spaces(string):
    global space_chars
    for i in range(len(string)):
        if string[i] not in space_chars:
            return string[i:]
    return ''

def if_upload_allowed_in(path, cfg):
    upload_allowed = False
    for i in cfg.upload_allowed_paths.split('|'):
        if path.startswith(i):
            upload_allowed = True
            break
    return upload_allowed

illegal_chars = [chr(x) for x in range(32)] + ['/', '\\', ':', '?', '*', '"', '<', '>', '|', '{.', '.}', '{:', ':}']
def purify_filename(filename) -> str:
    global illegal_chars
    for i in illegal_chars:
        filename = filename.replace(i, '_')
    return filename
