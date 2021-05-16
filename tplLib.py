
from scriptLib import StandardCommands, CommandsMap
from classesLib import Page, MacroResult, MacroParams, MacroToCallable
from helpers import read_ini, purify, recover, replacepairs, smartsize, concat_dict
import os, datetime

class MacroNotClosedProperly(Exception):
    """ Exception: Macro not closed properly """

class TooManyRecurs(Exception):
    """ Too many recurs in macro execution """

class TplInterpreter():
    class Section():
        def __init__(self, content: str, params: list, symbols: dict):
            self.content = content
            self.params = params
            self.symbols = symbols
    class Handler(CommandsMap):
        def __init__(self, vfs_manager=None, account_manager=None, settings_manager=None):
            self.vfs_manager = vfs_manager
            self.account_manager = account_manager
            self.settings_manager = settings_manager
            super().__init__()
        def __getitem__(self, name):
            return self.commands_map[name] if name in self.commands_map else self.commands_map['_unsupported']
        def __setitem__(self, key, value):
            self.commands_map[key] = value
    def __init__(self, tpl_file='hfs.tpl', vfs_manager=None, account_manager=None, settings_manager=None):
        self.handler = self.Handler(vfs_manager, account_manager, settings_manager)
        self.symbols = {
            'style': self.handler.sym_style,
            'user': self.handler.sym_user,
            'login-link': lambda p: self.get_section('login-link', p, True, True),
            'loggedin': lambda p: self.get_section('loggedin', p, True, True),
            'ip': lambda p: MacroResult(p.request.host),
            'version': lambda p: MacroResult('0.0.1'),
            'timestamp': lambda p: MacroResult(str(datetime.datetime.now())),
            'uptime': lambda p: MacroResult(str(datetime.datetime.now())),
            'connections': lambda p: MacroResult('0'),
            'speed-out': lambda p: MacroResult('0'),
            'speed-in': lambda p: MacroResult('0'),
            'total-out': lambda p: MacroResult('0'),
            'total-in': lambda p: MacroResult('0'),
            'total-downloads': lambda p: MacroResult('0'),
            'total-uploads': lambda p: MacroResult('0'),
            'number-addresses': lambda p: MacroResult('0'),
            'number-addresses-downloading': lambda p: MacroResult('0'),
            'build': lambda p: MacroResult('001'),
            'sequencial': lambda p: MacroResult('0'),
            'number-addresses-ever': lambda p: MacroResult('0'),
            'port': lambda p: MacroResult('80'),
            'folder': lambda p: MacroResult(p.request.path if p.request != None else ''),
            'encoded-folder': lambda p: MacroResult(purify(p.request.path) if p.request != None else '')
        }
        self.sections = {
            '': self.Section('', [], {
                'files': lambda p: self.get_section('files', p, True, True),
                'up': lambda p: self.get_section('up', p, True, True),
                'upload-link': lambda p: self.get_section('upload-link', p, True, True),
                'host': lambda p: MacroResult(p.request.host),
                'number': lambda p: MacroResult(str(len(os.listdir(p.request.path)))),
                'number-files': lambda p: MacroResult(str(len(list(filter(lambda x: os.path.isfile(x), os.listdir(p.request.path)))))),
                'number-folders': lambda p: MacroResult(str(len(list(filter(lambda x: os.path.isdir(x), os.listdir(p.request.path)))))),
                'total-size': lambda p: MacroResult('0'),
                'total-kbytes': lambda p: MacroResult('0'),
                'total-bytes': lambda p: MacroResult('0'),
                'build-time': lambda p: MacroResult('0'),
                'list': self.get_list,
            }),
            'style': self.Section('', ['public'], {}),
            'login-link': self.Section('', [], {}),
            'loggedin': self.Section('', [], {}),
            'up': self.Section('', [], {}),
            'file': self.Section('', [], {}),
            'folder': self.Section('', [], {}),
            'link': self.Section('', [], {}),
            'files': self.Section('', [], {
                'list': self.get_list,
                'item-archive': lambda p: self.get_section('item-archive', p, True, True),
            }),
            'nofiles': self.Section('', [], {}),
            'comment': self.Section('', [], {}),
            'folder-comment': self.Section('', [], {}),
            'newfile': self.Section('', [], {}),
            'upload-link': self.Section('', [], {}),
            'upload-file': self.Section('', [], {}),
            'upload-results': self.Section('', [], {}),
            'upload-success': self.Section('', [], {}),
            'upload-failed': self.Section('', [], {}),
            'progress': self.Section('', [], {}),
            'progress-download-file': self.Section('', [], {}),
            'progress-upload-file': self.Section('', [], {}),
            'progress-no-files': self.Section('', [], {}),
            'upload+progress': self.Section('', [], {}),
            'error-page': self.Section('', [], {}),
            'overload': self.Section('', [], {}),
            'unauthorized': self.Section('', [], {}),
            'deny': self.Section('', [], {}),
            'ban': self.Section('', [], {}),
            'max contemp downloads': self.Section('', [], {}),
            'not found': self.Section('', [], {}),
            'item-archive': self.Section('', [], {}),
            'protected': self.Section('', [], {}),
            'special:strings': self.Section('', [], {}),
            'special:alias': self.Section('', [], {})
        }
        f = open(tpl_file, 'r', encoding='utf-8')
        c = '\n' + f.read()
        f.close()
        s = c.split('\n[')
        for i in s:
            t = i.split(']\n', 1)
            if len(t) <= 1:
                continue
            p = t[0].split('|')
            for j in p[0].split('='):
                j = j.strip()
                if len(j) > 0:
                    if j[0] == '+':
                        j = j[1:]
                if j not in self.sections:
                    self.sections[j] = self.Section('', [], {})
                self.sections[j].content += t[1]
                self.sections[j].params = p
        self.translations = {}
        for i in self.get_section('special:strings', MacroParams([], self, {}, None, None, None), True, True).content.split('\n'):
            pair = i.split('=', 1)
            if len(pair) < 2:
                continue
            self.translations[pair[0]] = pair[1]
        alias_from_txt = read_ini('alias.txt')
        for i in alias_from_txt:
            self.handler[i] = MacroToCallable(alias_from_txt[i], self)
        for i in self.get_section('special:alias', MacroParams([], self, {}, None, None, None), False, True).content.split('\n'):
            pair = i.split('=', 1)
            if len(pair) < 2:
                continue
            self.handler[pair[0]] = MacroToCallable(pair[1], self)
    def get_section(self, sec_name: str, param: MacroParams, do_parse=True, force=False) -> Page:
        status = 404
        section = self.sections['not found']
        if sec_name in self.sections:
            status = 200
            section = self.sections[sec_name]
            if 'public' not in section.params and sec_name != '' and not force:
                status = 404
                section = self.sections['not found']
        result = self.parse_section(section, param) if do_parse else MacroResult(section.content)
        if 'Location' in result.headers:
            if result.headers['Location'] != param.request.path:
                status = 302
        result.headers['Server'] = 'PHFS/0.0.1'
        return Page(result.content, status, result.disconnect, result.headers, result.cookies)
    def get_list(self, param: MacroParams):
        _file = self.get_section('file', param, False, True)
        _folder = self.get_section('folder', param, False, True)
        _link = self.get_section('link', param, False, True)
        scanresult = os.scandir(param.request.path)
        fileinfos = {   # for sorting
            'name': [],
            'ext': [],
            'modified': [],
            'added': [],
            'size': []
        }
        links = []
        with scanresult as i:
            for e in i:
                # if not (os.path.exists(e.path) and os.access(e.path, os.R_OK)):  # sometimes appears a non-exist or unreadable file
                #     continue
                stats = e.stat()
                url = purify(e.path + ('' if e.is_file() else '/'))
                name = e.name.replace('|', '&#124;')
                last_modified = str(datetime.datetime.fromtimestamp(stats.st_mtime)).split('.')[0]
                last_modified_dt = str(stats.st_mtime)
                size = smartsize(stats.st_size)
                symbols = concat_dict(param.symbols, {
                    'item-url': lambda p: MacroResult(url),
                    'item-name': lambda p: MacroResult(name),
                    'item-modified': lambda p: MacroResult(last_modified),
                    'item-modified-dt': lambda p: MacroResult(last_modified_dt),
                    'item-size': lambda p: MacroResult(size),
                    'item-comment': lambda p: MacroResult('')
                })
                links.append(self.parse_text(_file.content if e.is_file() else _folder.content, symbols, param).content)
        links.sort()
        return Page(''.join(links), 200)
    def unquote(self, content, symbols, param: MacroParams, do_parse=True) -> MacroResult:
        if content[0:2] == '{:' and content[-2:] == ':}':
            content = content[2:-2]
        symbols = concat_dict(symbols, param.symbols)
        return self.parse_text(content, symbols, param) if do_parse else MacroResult(content)
    def parse_text(self, content: str, symbols: dict, param: MacroParams) -> MacroResult:
        symbols = concat_dict(self.symbols, symbols)
        for i in symbols:
            if '%%%s%%' % i in content:
                content = content.replace('%%%s%%' % i, symbols[i](MacroParams([i], self, symbols, param.request, param.vfs_manager, param.settings_manager)).content)
        macro_level = 0
        quote_level = 0
        position = 0
        length = len(content)
        full_macro = ['']
        broken = False
        disconnect = False
        headers = {
            'Server': 'PHFS/0.0.1'
        }
        cookies = []
        while position < length:
            # char0 = content[position]
            mark0 = content[position:position + 2]
            if mark0 == '{.' and quote_level == 0:
                macro_level += 1
                if macro_level > 100:
                    raise TooManyRecurs
            elif mark0 == '.}' and quote_level == 0:
                while position >= 0:
                    char1 = content[position]
                    mark1 = content[position:position + 2]
                    if mark1 == '{.' and quote_level == 0:
                        macro_level -= 1
                        full_macro = list(reversed(full_macro))
                        full_macro[0] = full_macro[0][1:]
                        full_macro[-1] = full_macro[-1][0:-1]
                        result = MacroResult('')
                        if not (broken or disconnect):
                            result = self.exec_macro(full_macro, symbols, param)
                            if result.break_exec:
                                broken = True
                            if result.disconnect:
                                disconnect = True
                            for i in result.headers:
                                headers[i] = result.headers[i]
                            for i in result.cookies:
                                cookies.append(i)
                        macro_str = '{.' + '|'.join(full_macro) + '.}'
                        content = content.replace(macro_str, result.content, 1)
                        for i in symbols:
                            if '%%%s%%' % i in content:
                                content = content.replace('%%%s%%' % i, symbols[i](MacroParams([i], self, symbols, param.request, param.vfs_manager, param.settings_manager)).content)
                        length = len(content)
                        full_macro = ['']
                        break
                    elif mark1 == '{:':
                        quote_level += 1
                    elif mark1 == ':}':
                        quote_level -= 1
                    if char1 == '|' and quote_level == 0:
                        full_macro.append('')
                    else:
                        full_macro[-1] = char1 + full_macro[-1]
                    if position == 0:
                        raise MacroNotClosedProperly
                    position -= 1
                continue
            elif mark0 == '{:':
                quote_level += 1
            elif mark0 == ':}':
                quote_level -= 1
            position += 1
        if macro_level != 0 or quote_level != 0:
            print(macro_level, quote_level)
            raise MacroNotClosedProperly
        return MacroResult(content, broken, disconnect, headers, cookies)
    def parse_section(self, section, param) -> MacroResult:
        symbols = concat_dict(section.symbols, param.symbols)
        return self.parse_text(section.content, symbols, param)
    shortcuts = {
        '!': 'translation',
        '$': 'section',
        '?': 'urlvar',
        '^': 'call'
    }
    operation_signs = ('<>', '!=', '<=', '>=', '<', '>', '=')
    def to_normal_macro(self, params: list):
        params = list(map(lambda s: s.strip(), params))
        if params[0] == '':
            return params
        if params[0][0] in self.shortcuts:
            params.append(params[0][1:])
            params[0] = self.shortcuts[params[0][0]]
        else:
            for i in self.operation_signs:
                if i in params[0] and i != params[0]:   # TODO: {.?value = 1.} -> {.urlvar|value = 1.} -> {.=|{.urlvar|value.}|1.}
                    p = params[0].split(i)
                    params = [i, p[0], p[1]]
                    break
        params = list(map(lambda s: s.strip(), params))
        return params
    def exec_macro(self, params: list, symbols={}, param=None) -> MacroResult:
        # params = list(map(lambda x: x.strip(), params))
        params = self.to_normal_macro(params)
        # print(params, end=' \t-> \t')
        result = self.handler[params[0]](MacroParams(params, self, symbols, param.request, param.vfs_manager, param.settings_manager))
        # print(result.content)
        return result
