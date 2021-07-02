
import datetime, os, random, shutil, time

from classesLib import TplSection, UniParam, MacroResult, MacroToCallable, Page, ItemEntry, FileList, object_from_dict
from scriptLib import Commands
from helpersLib import replace_str, read_ini, concat_dict, concat_list, purify, smartsize, sort, join_path, strip_starting_spaces
from cfgLib import Config

class MacroNotClosedProperly(Exception):
    """ Exception: Macro not closed properly """

class TooManyRecurs(Exception):
    """ Exception: Too many recurs in macro execution """

class Interpreter():
    """ Template interpreter, manages:
        - Sections
        - String parsing
        - Macro execute (handler)
    """
    def __init__(self, tpl_file='hfs.tpl'):
        self.handler = Commands()
        self.uptime_start = time.time()
        self.cached_pages = {}
        self.symbols = {
            'style': self.handler.sym_style,
            'user': self.handler.sym_user,
            'login-link': lambda p: self.get_section('login-link', p, True, True),
            'loggedin': lambda p: self.get_section('loggedin', p, True, True),
            'ip': lambda p: MacroResult(p.request.host),
            'version': lambda p: MacroResult(Config.version),
            'timestamp': lambda p: MacroResult(str(datetime.datetime.now())),
            'uptime': lambda p: MacroResult(str(datetime.timedelta(seconds=round(time.time() - self.uptime_start)))),
            'connections': lambda p: MacroResult('0'),
            'speed-out': lambda p: MacroResult('0'),
            'speed-in': lambda p: MacroResult('0'),
            'total-out': lambda p: MacroResult('0'),
            'total-in': lambda p: MacroResult('0'),
            'total-downloads': lambda p: MacroResult('0'),
            'total-uploads': lambda p: MacroResult('0'),
            'number-addresses': lambda p: MacroResult('0'),
            'number-addresses-downloading': lambda p: MacroResult('0'),
            'build': lambda p: MacroResult(Config.build),
            'sequencial': lambda p: MacroResult('0'),
            'number-addresses-ever': lambda p: MacroResult('0'),
            'port': lambda p: MacroResult(Config.port),
            'folder': lambda p: MacroResult(join_path(p.request.path_virtual_dir, '/') if p.request != None else ''),
            'encoded-folder': lambda p: MacroResult(purify(join_path(p.request.path_virtual_dir, '/')) if p.request != None else '')
        }
        self.sections = object_from_dict({
            '_empty': TplSection('', [], {}),
            '': TplSection('', ['public'], {
                'files': lambda p: self.get_page('files', p),
                'up': lambda p: self.get_section('up', p, True, True),
                'upload-link': lambda p: self.get_section('upload-link', p, True, True),
                'host': lambda p: MacroResult(p.request.host),
                'number': lambda p: MacroResult(str(p.filelist.count)),
                'number-files': lambda p: MacroResult(str(p.filelist.count_files)),
                'number-folders': lambda p: MacroResult(str(p.filelist.count_folders)),
                'total-size': lambda p: MacroResult(smartsize(sum([os.stat(x.path).st_size for x in p.filelist.items]))),
                'total-kbytes': lambda p: MacroResult(str(sum([os.stat(x.path).st_size for x in p.filelist.items]) // 1024)),
                'total-bytes': lambda p: MacroResult(str(sum([os.stat(x.path).st_size for x in p.filelist.items]))),
                'list': self.get_list,
                'folder-item-comment': lambda p: MacroResult('')
            }),
            'files': TplSection('', [], {
                'list': self.get_list,
                'item-archive': lambda p: self.get_section('item-archive', p, True, True),
            }),
            'nofiles': TplSection('', [], {}),
            'upload': TplSection('', [], {
                'diskfree': lambda p: MacroResult(smartsize(shutil.disk_usage(p.request.path_real_dir).free)),
            })
        })
        f = open(tpl_file, 'r', encoding='utf-8')
        c = '\n' + f.read()
        f.close()
        s = c.split('\n[')
        for i in s:
            t = i.split(']\n', 1)
            if len(t) <= 1:
                continue
            plus = False
            prepend = False
            if t[0][0:1] == '+':
                plus = True
                t[0] = t[0][1:]
            elif t[0][0:1] == '^':
                prepend = True
                t[0] = t[0][1:]
            p = t[0].split('|')
            for j in p[0].split('='):
                j = j.strip()
                if j not in self.sections:
                    self.sections[j] = TplSection('', [], {})
                if plus:
                    self.sections[j].content += t[1].strip('\n') + '\n'
                elif prepend:
                    self.sections[j].content = t[1] + self.sections[j].content.strip('\n') + '\n'
                else:
                    self.sections[j].content = t[1].strip('\n') + '\n'
                    self.sections[j].params = p[1:]
        self.translations = {}
        for i in self.sections.get('special:strings', self.sections['_empty']).content.split('\n'):
            pair = i.split('=', 1)
            if len(pair) < 2:
                continue
            self.translations[pair[0]] = pair[1]
        alias_from_txt = read_ini('alias.txt')
        for i in alias_from_txt:
            self.handler[i] = MacroToCallable(alias_from_txt[i], UniParam([], interpreter=self), True)
        for i in self.sections.get('special:alias', self.sections['_empty']).content.split('\n'):
            pair = i.split('=', 1)
            if len(pair) < 2:
                continue
            self.handler[pair[0]] = MacroToCallable(pair[1], UniParam([], interpreter=self), True)
        return
    def get_list(self, param: UniParam):
        """ Get filelist, called by symbol `%list%`.  
        """
        page_content = param.filelist.to_list(param)
        param.request.listing_completed = True
        return Page(page_content, 200)
    def get_section(self, section_name: str, param: UniParam, do_parse=True, force=False) -> MacroResult:
        """ Get a section from template. What this returns is a `MacroResult`.   
            `section_name`: Name of section.  
            `param`: `UniParam` for parsing macros and symbols.  
            `do_parse`: Parse the content?  
            `force`: Get this section even if not public?
        """
        section: TplSection = self.sections.get(section_name, None)
        if section == None:
            return None
        param.symbols = concat_dict(param.symbols, section.symbols)
        return self.parse_text(section.content, param) if do_parse else MacroResult(section.content)
    def section_to_page(self, section_name, param: UniParam):
        # Deep copy param, prevent modifying original one
        uni_param = UniParam(param.params, interpreter=param.interpreter, request=param.request, filelist=param.filelist, statistics=param.statistics)
        section = self.get_section(section_name, uni_param, True, True)
        if section == None:
            return self.get_page('error-page', UniParam(['not found', 404], interpreter=self, request=param.request))
        status = 200
        if 'Location' in section.headers:
            status = 302
        return Page(section.content, status, section.headers)
    def get_page(self, page_name: str, param: UniParam) -> Page:
        uni_param = param
        if page_name == '':
            page = self.section_to_page('', param)
            page.content = replace_str(page.content, '%build-time%', str(round(time.time() - param.request.build_time_start, 3)))
            return page
        elif page_name == 'files':
            if param.filelist.count == 0:
                nofiles = self.get_section('nofiles', param, True, True)
                return Page(nofiles.content, 200)
            return self.section_to_page('files', param)
        elif page_name == 'list':
            return self.get_list(uni_param)
        elif page_name == 'upload':
            return self.section_to_page('upload', param)
        elif page_name == 'upload-results':
            page = self.section_to_page('upload-results', param)
            _success = self.get_section('upload-success', uni_param, False, True)
            _failed = self.get_section('upload-failed', uni_param, False, True)
            uploaded_files = []
            upload_result = param.params[0]
            assert type(upload_result) == dict, 'param.params[0] is not a dict'
            for i in upload_result:
                result = upload_result[i]
                if result[0] == True:
                    uploaded_files.append(self.parse_text(_success.content, UniParam([], symbols={
                        'item-name': lambda p: MacroResult(i),
                        'item-size': lambda p: MacroResult(smartsize(os.stat(param.request.path_real + i).st_size)),
                        'speed': lambda p: MacroResult('0')
                    }, interpreter=self, request=param.request)).content)
                else:
                    uploaded_files.append(self.parse_text(_failed.content, UniParam([], symbols={
                        'item-name': lambda p: MacroResult(i),
                        'reason': lambda p: MacroResult(result[1])
                    }, interpreter=self, request=param.request)).content)
            page.content = replace_str(page.content, '%uploaded-files%', ''.join(uploaded_files))
            return page
        elif page_name == 'error-page':
            error_type = param.params[0]
            error_status = param.params[1]
            base_page = self.get_section('error-page', UniParam([], symbols={}, request=param.request, interpreter=self, statistics=param.statistics))
            content = self.get_section(error_type, UniParam([], symbols={}, request=param.request, interpreter=self, statistics=param.statistics))
            headers = concat_dict(base_page.headers, content.headers)
            if 'Location' in headers:
                error_status = 302
            return Page(replace_str(base_page.content, '%content%', content.content), error_status, headers)
    def parse_symbols(self, text: str, param: UniParam, *symbols):
        for i in symbols:
            for j in i:
                if '%%%s%%' % j in text:
                    text = text.replace('%%%s%%' % j, i[j](param).content)
        return text
    def parse_text(self, text: str, param: UniParam) -> MacroResult:
        """ Parse a string and apply symbols and macros
        """
        text = self.parse_symbols(text, param, param.symbols, self.symbols)
        macro_level = 0
        quote_level = 0
        position = 0
        newlines = 0
        last_newline_at = 0
        length = len(text)
        full_macro = ['']
        broken = False
        disconnect = False
        headers = {}
        while position < length:
            last_macro_at = position
            char0 = text[position]
            mark0 = text[position:position + 2]
            if char0 == '\n':
                newlines += 1
                last_newline_at = position
            if mark0 == '{.' and quote_level == 0:
                macro_level += 1
                if macro_level > 100:
                    raise TooManyRecurs('Too many recurs at line %d, column %d' % (newlines, position - last_newline_at))
            elif mark0 == '.}' and quote_level == 0:
                while position >= 0:
                    char1 = text[position]
                    mark1 = text[position:position + 2]
                    if char1 == '\n':
                        newlines -= 1
                        last_newline_at = position
                    if mark1 == '{.' and quote_level == 0:
                        macro_level -= 1
                        full_macro = list(reversed(full_macro))
                        full_macro[0] = full_macro[0][1:]
                        full_macro[-1] = full_macro[-1][0:-1]
                        result = MacroResult('')
                        if not (broken or disconnect):
                            result = self.exec_macro(full_macro, param)
                            if result.do_break:
                                broken = True
                            if result.disconnect:
                                disconnect = True
                                return MacroResult('', do_break=True, disconnect=True, headers=headers)
                            for i in result.headers:
                                headers[i] = result.headers[i]
                        macro_str = '{.' + '|'.join(full_macro) + '.}'
                        text = replace_str(text, macro_str, result.content)
                        text = self.parse_symbols(text, param, param.symbols, self.symbols)
                        length = len(text)
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
                        raise MacroNotClosedProperly('Macro not closed properly at line %d, column %d' % (newlines, last_macro_at - last_newline_at))
                    position -= 1
                continue
            elif mark0 == '{:':
                quote_level += 1
            elif mark0 == ':}':
                quote_level -= 1
            position += 1
        if macro_level != 0 or quote_level != 0:
            print(macro_level, quote_level)
            raise MacroNotClosedProperly('Macro not closed properly')
        return MacroResult(text, do_break=broken, disconnect=disconnect, headers=headers)
    def unquote(self, text: str, param: UniParam, do_parse=True) -> MacroResult:
        if text[0:2] == '{:' and text[-2:] == ':}':
            text = text[2:-2]
        # text = strip_starting_spaces(text)    # No need
        # Deep copy param, prevent modifying original one
        uni_param = UniParam(param.params, interpreter=param.interpreter, request=param.request, filelist=param.filelist, statistics=param.statistics)
        return self.parse_text(text, uni_param) if do_parse else MacroResult(text)
    def is_quoted(self, text: str) -> bool:
        return text[0:2] == '{:' and text[-2:] == ':}'
    shortcuts = {
        '!': 'translation',
        '$': 'section',
        '?': 'urlvar',
        '^': 'call'
    }
    operation_signs = ('<>', '!=', '<=', '>=', '<', '>', '=')
    def to_normal_macro(self, params: list):
        params = [x.strip() for x in params]
        if params[0] == '':
            return params
        if params[0][0] in self.shortcuts:
            params.append(params[0][1:])
            params[0] = self.shortcuts[params[0][0]]
        for i in self.operation_signs:
            if i in params[0] and i != params[0]:
                p = params[0].split(i)
                params = [i, p[0], p[1]]
                break
        params = [x.strip() for x in params]
        return params
    def exec_macro(self, params: list, param: UniParam) -> MacroResult:
        params = self.to_normal_macro(params)
        if params[-1].split('/')[-1] == params[0] and len(params) > 2:
            params[-1] = '/'.join(params[-1].split('/')[0:-1])
        params = [strip_starting_spaces(x) for x in params]
        param.params = params
        result = self.handler[params[0]](param)
        return result
    