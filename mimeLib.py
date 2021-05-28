#!/usr/bin/python3

import re
from helpersLib import wildcard2re, read_ini

mimedict = {}   # This is master one. Will be inited.

# built-in
mimesheetA = {
    '*.htm;*.html': 'text/html',
    '*.jpg;*.jpeg;*.jpe': 'image/jpeg',
    '*.gif': 'image/gif',
    '*.png': 'image/png',
    '*.bmp': 'image/bmp',
    '*.ico': 'image/x-icon',
    '*.mpeg;*.mpg;*.mpe': 'video/mpeg',
    '*.mp3': 'audio/mpeg',
    '*.avi': 'video/x-msvideo',
    '*.tar': 'application/x-tar',
    '*.txt': 'text/plain',
    '*.css': 'text/css',
    '*.js':  'text/javascript'
}

def setmime(data: dict):
    for i in data:
        for j in i.split(';'):
            mimedict[j] = data[i]

setmime(mimesheetA)

# from ini
mimesheetB = read_ini('mime.ini')
setmime(mimesheetB)

# get mime
def getmime(url: str):
    if url[-1] == '/':
        return 'text/html'
    else:
        item = url.split('/')[-1]
        for i in mimedict:
            if re.match(wildcard2re(i), item):
                return mimedict[i]
    return 'text/html'