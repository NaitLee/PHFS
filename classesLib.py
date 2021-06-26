
import os, locale
from typing import Union
import datetime

from cfgLib import Config
from helpersLib import get_dirname, purify, concat_dict, smartsize, sort

class DictAsObject(dict):
    """ Let you use a dict like an object in JavaScript.  
        More to say, it's the ability to get a key with dot:
        ```
            obj[key] = value
            obj.key = value
        ```
    """
    def __init__(self, **kwargs):
        super().__init__(kwargs)
    def __getattr__(self, key):
        return self.get(key, None)
    def __setattr__(self, key, value):
        self[key] = value
        return

def object_from_dict(d: dict):
    """ Get a `DictAsObject` from a normal `dict`
    """
    n = DictAsObject()
    for i in d:
        n[i] = d[i]
    return n

class Page():
    """ A generated page.  
        `content`: Text representation of page.  
        `status`: Status code.  
        `headers`: Headers to add, as a `dict`.  
        `cookies`: Cookies to add, as a `list`.
    """
    content: str
    status: int
    headers: Union[dict, DictAsObject] = DictAsObject()
    def __init__(self, content: str, status: int, headers=DictAsObject(), cookies=[]):
        self.content = content
        self.status = status
        self.headers = headers
        self.cookies = cookies

class TplSection():
    """ A template section.  
        `content`: Text in this section.  
        `params`: Params of this section. e.g. public, no log.  
        `symbols`: Symbols of this section, which is a `dict` with callable values.
    """
    content: str
    params: list
    symbols: dict
    def __init__(self, content: str, params: list, symbols: dict):
        self.content = content
        self.params = params
        self.symbols = symbols

class UniParam():
    """ Universal params.  
        `params`: A `list` of params, used by macros etc.  
        `symbols`: A `dict` with callable values, used by interpreter.  
        `interpreter`: A `TplInterpreter` instance.  
        `request`: The WSGI request.  
        `filelist`: A `FileList` object.
    """
    params: list
    symbols: dict = {}
    interpreter = None
    request = None
    filelist = None
    def __init__(self, params: list, **kwargs):
        self.params = params
        for i in kwargs:
            setattr(self, i, kwargs[i])

class MacroResult():
    """ Macro result after executing.  
        `content`: Text representation of result.  
        `do_break`: Break macro execution?  
        `disconnect`: Disconnect this request?  
        `headers`: Headers to add, as a `dict`.  
        `cookies`: Cookies to add, as a `list`.
    """
    content: str
    do_break: bool = False
    disconnect: bool = False
    headers: dict = {}
    cookies: list = []
    def __init__(self, content: str, **kwargs):
        self.content = content
        for i in kwargs:
            setattr(self, i, kwargs[i])

class MacroToCallable():
    def __init__(self, macro_str: str, interpreter):
        if not (macro_str[0:2] == '{.' and macro_str[-2:] == '.}'):
            macro_str = '{.' + macro_str + '.}'
        self.macro_str = macro_str
        self.interpreter = interpreter
    def __call__(self, param: UniParam) -> MacroResult:
        new_str = self.macro_str    # Prevent changing original string
        for i, j in enumerate(param.params):
            new_str = new_str.replace('$' + str(i), j)
        return self.interpreter.parse_text(new_str, param)

class ItemEntry():
    """ A class that acts like `os.DirEntry`, but with more.
    """
    name: str
    path: str
    url: str
    _is_dir: bool
    _stat: os.stat_result
    def __init__(self, path_real: str, path_virtual: str, base_virtual_dir='/'):
        levels_real = path_real.split('/')
        self.name = levels_real[-2] if path_real[-1] == '/' else levels_real[-1]
        self.path = path_real
        self.url = path_virtual[len(base_virtual_dir):]
        self._is_dir = os.path.isdir(path_real)
        self._stat = os.stat(path_real)
    def is_file(self):
        return not self._is_dir
    def is_dir(self):
        return self._is_dir
    def stat(self):
        return self._stat

class FileList():
    """ A file list.  
        `items`: A `list` of `ItemEntry`.
    """
    items: list
    def __init__(self, items: list):
        self.items = items
        self.count = len(items)
        self.count_folders = len([True for x in items if x.is_dir()])
        self.count_files = self.count - self.count_folders
    def to_list(self, param: UniParam):
        interpreter = param.interpreter
        scanresult = self.items
        fileinfos_file = {   # for sorting
            'name': [],
            'ext': [],
            'modified': [],
            'added': [],
            'size': []
        }
        fileinfos_folder = {   # for sorting
            'name': [],
            'ext': [],
            'modified': [],
            'added': [],
            'size': []
        }
        _file = interpreter.sections.get('file', interpreter.sections['_empty'])
        _folder = interpreter.sections.get('folder', interpreter.sections['_empty'])
        _link = interpreter.sections.get('link', interpreter.sections['_empty'])
        links_file = []
        links_folder = []
        for e in scanresult:
            # if not (os.path.exists(e.path) and os.access(e.path, os.R_OK)):  # sometimes appears a non-exist or unreadable file
            #     continue
            stats = e.stat()
            url = purify(e.url + ('' if e.is_file() and e.url[-1] != '/' else '/'))
            name = e.name.replace('|', '&#124;')
            last_modified = str(datetime.datetime.fromtimestamp(stats.st_mtime)).split('.')[0]
            last_modified_dt = stats.st_mtime
            size = stats.st_size
            if e.is_file():
                fileinfos_file['name'].append(name)
                fileinfos_file['ext'].append(name.split('.')[-1])
                fileinfos_file['modified'].append(last_modified_dt)
                fileinfos_file['added'].append(last_modified_dt)
                fileinfos_file['size'].append(size)
                param.symbols = concat_dict(param.symbols, {
                    'item-url': lambda p: MacroResult(url),
                    'item-full-url': lambda p: MacroResult(url),
                    'item-name': lambda p: MacroResult(name),
                    'item-ext': lambda p: MacroResult(name.split('.')[-1]),
                    'item-modified': lambda p: MacroResult(last_modified),
                    'item-modified-dt': lambda p: MacroResult(str(last_modified_dt)),
                    'item-size': lambda p: MacroResult(smartsize(size)),
                    'item-comment': lambda p: MacroResult(''),
                    'item-icon': lambda p: MacroResult('')
                })
                links_file.append(interpreter.parse_text(_file.content, param).content)
            else:
                fileinfos_folder['name'].append(name)
                fileinfos_folder['ext'].append(name.split('.')[-1])
                fileinfos_folder['modified'].append(last_modified_dt)
                fileinfos_folder['added'].append(last_modified_dt)
                fileinfos_folder['size'].append(size)
                param.symbols = concat_dict(param.symbols, {
                    'item-url': lambda p: MacroResult(url),
                    'item-full-url': lambda p: MacroResult(url),
                    'item-name': lambda p: MacroResult(name),
                    'item-ext': lambda p: MacroResult(name.split('.')[-1]),
                    'item-modified': lambda p: MacroResult(last_modified),
                    'item-modified-dt': lambda p: MacroResult(str(last_modified_dt)),
                    'item-size': lambda p: MacroResult(smartsize(size)),
                    'item-comment': lambda p: MacroResult(''),
                    'item-icon': lambda p: MacroResult('')
                })
                links_folder.append(interpreter.parse_text(_folder.content, param).content)
        sorting_comp = 'name'
        sort_encoding = 'utf-8'
        if Config.sort_encoding == '':
            sort_encoding = locale.getpreferredencoding()
        else:
            sort_encoding = Config.sort_encoding
        sorting_func = lambda a, b: int(sorted([a, b], key=lambda x: x.encode(sort_encoding)) != [a, b])
        if 'sort' in param.request.args:
            sort_by = param.request.args['sort']
            rev = 'rev' in param.request.args
            if sort_by == 'e' and not rev:
                sorting_comp = 'ext'
                sorting_func = lambda a, b: int(sorted([a, b]) != [a, b])
            elif sort_by == 'n' and not rev:
                sorting_comp = 'name'
                sorting_func = lambda a, b: int(sorted([a, b], key=lambda x: x.encode(sort_encoding)) != [a, b])
            elif sort_by == 't' and not rev:
                sorting_comp = 'modified'
                sorting_func = lambda a, b: a - b
            elif sort_by == 's' and not rev:
                sorting_comp = 'size'
                sorting_func = lambda a, b: a - b
            elif sort_by == '!e' or (sort_by == 'e' and rev):
                sorting_comp = 'ext'
                sorting_func = lambda a, b: int(sorted([a, b]) == [a, b])
            elif sort_by == '!n' or (sort_by == 'n' and rev):
                sorting_comp = 'name'
                sorting_func = lambda a, b: int(sorted([a, b], key=lambda x: x.encode(sort_encoding)) == [a, b])
            elif sort_by == '!t' or (sort_by == 't' and rev):
                sorting_comp = 'modified'
                sorting_func = lambda a, b: b - a
            elif sort_by == '!s' or (sort_by == 's' and rev):
                sorting_comp = 'size'
                sorting_func = lambda a, b: b - a
        links_folder = sort(links_folder, fileinfos_folder[sorting_comp], sorting_func)
        links_file = sort(links_file, fileinfos_file[sorting_comp], sorting_func)
        page_content = ''.join(links_folder) + ''.join(links_file)
        return page_content
