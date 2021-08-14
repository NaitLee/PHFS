
import datetime, time, re, os, math, urllib.parse, shutil, hashlib
from classesLib import MacroResult, UniParam, MacroToCallable
from helpersLib import concat_dict, wildcard2re, if_upload_allowed_in, float_to_str, is_number, join_path, smartcopy, smartmove
from cfgLib import Config, Account

class Commands():
    TRUE = '1'
    FALSE = ''
    FALSE_VALUES = ('', '0', '0.0')
    def __init__(self):
        self.global_vars = {}
        self.commands_map = {
            'sym_style': self.sym_style,
            'sym_user': self.sym_user,
            'if': self.macro_if,
            'if not': self.macro_if_not,
            'not': self.macro_not,
            'and': self.macro_and,
            'or': self.macro_or,
            'xor': self.macro_xor,
            'switch': self.macro_switch,
            'for': self.macro_for,
            'for each': self.macro_for_each,
            'while': self.macro_while,
            'after the list': self.after_the_list,
            'dequote': self.dequote,
            'call': self.macro_call,
            'break': self.macro_break,
            'replace': self.replace,
            'translation': self.translation,
            'section': self.section,
            'comment': self.comment,
            'breadcrumbs': self.breadcrumbs,
            'header': self.header,
            'substring': self.substring,
            '=': self.equal,
            '!=': self.not_equal,
            '<>': self.not_equal,
            '>': self.greater_than,
            '<': self.lesser_than,
            '>=': self.greater_or_equal_than,
            '<=': self.lesser_or_equal_than,
            'set': self.macro_set,
            'inc': self.inc,
            'dec': self.dec,
            'disconnect': self.disconnect,
            'add header': self.add_header,
            'time': self.time,
            'length': self.length,
            'get': self.get,
            'match': self.match,
            'regexp': self.regexp,
            'filesize': self.filesize,
            'urlvar': self.urlvar,
            'postvar': self.postvar,
            'no pipe': self.no_pipe,
            'cut': self.cut,
            'calc': self.calc,
            'chr': self.macro_chr,
            'js encode': self.js_encode,
            'count': self.macro_count,
            'from table': self.from_table,
            'set table': self.set_table,
            'round': lambda p: MacroResult(float_to_str(round(float(p[1]), int(p[2])))),
            'add': lambda p: MacroResult(float_to_str(float(p[1]) + float(p[2]))),
            'sub': lambda p: MacroResult(float_to_str(float(p[1]) - float(p[2]))),
            'mul': lambda p: MacroResult(float_to_str(float(p[1]) * float(p[2]))),
            'div': lambda p: MacroResult(float_to_str(float(p[1]) / float(p[2]))),
            'mod': lambda p: MacroResult(float_to_str(int(p[1]) % int(p[2]))),
            'min': lambda p: MacroResult(float_to_str(min([float(x) for x in p.params[1:]]))),
            'max': lambda p: MacroResult(float_to_str(max([float(x) for x in p.params[1:]]))),
            'count substring': lambda p: MacroResult(str(p[1].count(p[2]))),
            'repeat': lambda p: MacroResult(p[2] * int(p[1])),
            'lower': lambda p: MacroResult(p[1].lower()),
            'upper': lambda p: MacroResult(p[1].upper()),
            'trim': lambda p: MacroResult(p[1].strip()),
            'encodeuri': lambda p: MacroResult(urllib.parse.quote(p[1])),
            'decodeuri': lambda p: MacroResult(urllib.parse.unquote(p[1])),
            'convert': lambda p: MacroResult(p[3]),
            'force ansi': lambda p: MacroResult(p[1]),
            'maybe utf8': lambda p: MacroResult(p[1]),
            'cookie': self.cookie,
            'load': self.load,
            'save': self.save,
            'append': self.append,
            'delete': self.delete,
            'rename': self.rename,
            'md5 file': self.md5_file,
            'copy': self.copy,
            'move': self.move,
            'chdir': self.chdir,
            'mkdir': self.mkdir,
            'exists': self.exists,
            'is file': self.is_file,
            'filename': self.filename,
            'filepath': self.filepath,
            'filetime': self.filetime,
            'disk free': lambda p: MacroResult(shutil.disk_usage(p.request.path_real_dir).free),
            'dir': self.macro_dir,
            '_unsupported': self._unsupported
        }
    def __getitem__(self, key):
        return self.commands_map.get(key, self.commands_map['_unsupported'])
    def __setitem__(self, key, value):
        self.commands_map[key] = value
        return
    def _judge(self, value: str) -> bool:
        return False if value.strip() in self.FALSE_VALUES else True
    def _bool(self, value: bool) -> str:
        return self.TRUE if value else self.FALSE
    def _unsupported(self, param: UniParam):
        print('Warning: Unsupported macro "%s"' % param[0])
        return MacroResult('')
    def sym_style(self, param: UniParam):
        return param.interpreter.get_section('style', param, True, True)
    def sym_user(self, param: UniParam):
        return MacroResult(param.statistics.accounts.get(param.request.cookies.get('HFS_SID_', ''), ('', param.request.host))[0])
    def macro_call(self, param: UniParam):
        p = param.params
        if self._have_variable(p[1], param):
            return MacroResult(self._get_variable(p[1], param))
        elif p[1] in param.interpreter.handler:
            param.params = param[1:]
            return MacroResult(param.interpreter.handler(param))
    def _get_optional_params(self, param: UniParam, *params):
        optional_params = {}
        for i in params:
            for j in param.params:
                if j.startswith(i + '='):
                    optional_params[i] = j[len(i) + 1:]
        return optional_params
    def _set_variable(self, key: str, value: str, param: UniParam) -> str:
        if key[0:1] == '#':
            param.statistics.variables[key] = value
        else:
            param.request.variables[key] = value
    def _get_variable(self, key: str, param: UniParam) -> str:
        if key in param.request.variables:
            return param.request.variables.get(key, self.FALSE)
        elif key in param.statistics.variables:
            return param.statistics.variables.get(key, self.FALSE)
    def _have_variable(self, key: str, param: UniParam) -> bool:
        return key in param.request.variables or key in param.statistics.variables
    def _get_existing_filename(self, path: str):
        # Priority: in VFS (base_path), relative to (P)HFS cd path, real path
        predict_paths = [
            join_path(Config.base_path, path),
            path[1:] if path[0:1] == '/' else path,
            path
        ]
        for i in predict_paths:
            if os.path.exists(i):
                return i
        return None
    def _return_empty(self):
        return MacroResult('')
    def load(self, param: UniParam):
        optional_params = self._get_optional_params(param, 'from', 'size', 'to', 'var')
        p_from = 0
        p_to = 0
        p_size = 0
        data = ''
        path = self._get_existing_filename(param[1])
        if path != None:
            p_from = int(optional_params.get('from', '0'))
            p_to = int(optional_params.get('to', str(os.path.getsize(path))))
            p_size = int(optional_params.get('size', str(p_to - p_from)))
            f = open(path, 'rb')
            f.seek(p_from)
            data = f.read(p_size).decode('utf-8')
            f.close()
        if optional_params.get('var', '') != '':
            param.request.variables[optional_params['var']] = data
            data = ''
        return MacroResult(data)
    def save(self, param: UniParam):
        optional_params = self._get_optional_params(param, 'var')
        path = self._get_existing_filename(param[1])
        f = open(path or param[1], 'w', encoding='utf-8')
        if optional_params.get('var', '') == '':
            f.write(param[2])
        else:
            f.write(param.request.variables[optional_params['var']])
        f.close()
        return self._return_empty()
    def append(self, param: UniParam):
        path = self._get_existing_filename(param[1])
        f = open(path or param[1], 'a', encoding='utf-8')
        f.write(param[2])
        f.close()
        return self._return_empty()
    def delete(self, param: UniParam):
        path = self._get_existing_filename(param[1])
        shutil.rmtree(path, True)
        return self._return_empty()
    def rename(self, param: UniParam):
        path = self._get_existing_filename(param[1])
        if path != None:
            os.rename(path, os.path.dirname(path) + param[2])
        return self._return_empty()
    def md5_file(self, param: UniParam):
        path = self._get_existing_filename(param[1])
        hash_str = ''
        if path != None:
            hash_str = hashlib.md5(path).hexdigest()
        return MacroResult(hash_str)
    def copy(self, param: UniParam):
        path = self._get_existing_filename(param[1])
        if path != None:
            smartcopy(path, param[2])
        return self._return_empty()
    def move(self, param: UniParam):
        path = self._get_existing_filename(param[1])
        if path != None:
            smartmove(path, param[2])
        return self._return_empty()
    def chdir(self, param: UniParam):
        path = self._get_existing_filename(param[1])
        if path != None:
            os.chdir(param[1])
        return self._return_empty()
    def mkdir(self, param: UniParam):
        path = self._get_existing_filename(param[1])
        os.makedirs(path or param[1], exist_ok=True)
        return self._return_empty()
    def exists(self, param: UniParam):
        path = self._get_existing_filename(param[1])
        return MacroResult(self._bool(path != None))
    def is_file(self, param: UniParam):
        path = self._get_existing_filename(param[1])
        return MacroResult(self._bool(os.path.isfile(path)))
    def filename(self, param: UniParam):
        return MacroResult(os.path.basename(param[1]))
    def filesize(self, param: UniParam):
        size = 0
        path = self._get_existing_filename(param[1])
        if path != None:
            size = os.path.getsize(path)
        return MacroResult(str(size))
    def filepath(self, param: UniParam):
        return MacroResult(os.path.dirname(param[1]))
    def filetime(self, param: UniParam):
        return MacroResult(os.path.getmtime(param[1]))
    def macro_dir(self, param: UniParam):
        optional_params = self._get_optional_params(param, 'separator')
        separator = optional_params.get('separator', '|')
        path = self._get_existing_filename(param[1])
        result = ''
        if path != None:
            result = separator.join(os.listdir(path))
        return MacroResult(result)
    def calc(self, param: UniParam):
        # TODO
        return MacroResult('0')
    def macro_chr(self, param: UniParam):
        result = ''
        for i in param.params[1:]:
            if i[0:1].lower() == 'x':
                result = result + chr(int(i[1:], 16))
            else:
                result = result + chr(int(i, 10))
        return MacroResult(result)
    def js_encode(self, param: UniParam):
        param.params.append('\'"')
        result = param[1]
        for i in param[2]:
            result = result.replace(i, '\\x%02x' % ord(i))
        return MacroResult(result)
    def macro_count(self, param: UniParam):
        counts = param.request.counts
        if param[1] in counts:
            counts[param[1]] += 1
            return MacroResult(str(counts[param[1]]))
        else:
            counts[param[1]] = 0
            return MacroResult('0')
    def from_table(self, param: UniParam):
        return MacroResult(param.request.table.get(param[1], {}).get(param[2], ''))
    def set_table(self, param: UniParam):
        table = param.request.table
        table_name = param[1]
        key, value = param[2].split('=', 2)
        if table_name not in table:
            table[table_name] = {}
        table[table_name][key] = value
        return self._return_empty()
    def no_pipe(self, param: UniParam):
        return MacroResult('{:|:}'.join(param[1:]))
    def substring(self, param: UniParam):
        # Case sensitivity always true
        string: str = param[3]
        start = string.find(param[1]) + len(param[1])
        end = string.find(param[2])
        if start in (0, len(string) - 1):
            start = 0
        if end in (0, -1):
            end = len(string)
        optional_params = self._get_optional_params(param, 'include')
        include = optional_params.get('include', '1')
        result = string[start:end]
        if include == '1':
            result = param[1] + result
        elif include == '2':
            result = result + param[2]
        elif include == '1+2':
            result = param[1] + result + param[2]
        return MacroResult(result)
    def dequote(self, param: UniParam):
        return param.interpreter.unquote(param[1], param, True)
    def after_the_list(self, param: UniParam):
        # Since filelist is done just when first symbol parse, this currently does no work
        return param.interpreter.unquote(param[1], param, True) if param.request.listing_completed else MacroResult('')
    def macro_for(self, param: UniParam):
        p = param.params
        var_name = p[1]
        var_step = int(p[4]) if len(p) > 5 else 1
        var_range = range(int(p[2]), int(p[3]) + 1, var_step)
        macro_body = param.interpreter.unquote(p[5] if len(p) > 5 else p[4], param, False).content
        result = []
        for i in var_range:
            self._set_variable(var_name, str(i), param)
            result.append(param.interpreter.parse_text(macro_body, param))
        return MacroResult(''.join([x.content for x in result]))
    def macro_for_each(self, param: UniParam):
        p = param.params
        var_name = p[1]
        var_range = p[2:-1]
        macro_body = param.interpreter.unquote(p[-1], param, False).content
        result = []
        for i in var_range:
            self._set_variable(var_name, i, param)
            result.append(param.interpreter.parse_text(macro_body, param))
        return MacroResult(''.join([x.content for x in result]))
    def macro_while(self, param: UniParam):
        is_variable = not param.interpreter.is_quoted(param[1])
        result = []
        while True:
            if is_variable:
                if not self._judge(self._get_variable(param[1], param)):
                    break
            else:
                if not self._judge(param.interpreter.unquote(param[1], param, True).content):
                    break
            result.append(param.interpreter.unquote(param[2], param, True))
        return MacroResult(''.join([x.content for x in result]))
    def macro_and(self, param: UniParam):
        p = param.params
        status = self.FALSE
        for i in range(1, len(p) - 1):
            status = p[i] and p[i + 1]
        return MacroResult(status)
    def macro_or(self, param: UniParam):
        p = param.params
        status = self.FALSE
        for i in range(1, len(p) - 1):
            status = p[i] or p[i + 1]
        return MacroResult(status)
    def macro_xor(self, param: UniParam):
        return MacroResult(self._bool(self._judge(param[1]) == self._judge(param[2])))
    def urlvar(self, param: UniParam):
        return MacroResult(param.request.args.get(param[1], self.FALSE))
    def postvar(self, param: UniParam):
        return MacroResult(param.request.form.get(param[1], self.FALSE))
    def cookie(self, param: UniParam):
        optional_params = self._get_optional_params(param, 'value', 'expires', 'path')
        result = ''
        headers = {}
        if 'value' not in optional_params:
            result = param.request.cookies.get(param[1], self.FALSE)
        else:
            headers['Set-Cookie'] = '; '.join(('%s=%s' % (param[1], optional_params['value']), 'expires=' + optional_params.get('expires', ''), 'path=' + optional_params.get('path', '/')))
        return MacroResult(result, headers=headers)
    def macro_set(self, param: UniParam):
        self._set_variable(param[1], param[2], param)
        return self._return_empty()
    def inc(self, param: UniParam):
        if len(param.params) > 2:
            self._set_variable(param[1], float_to_str(float(self._get_variable(param[1], param)) + float(param[2])), param)
        elif len(param.params) == 2:
            self._set_variable(param[1], float_to_str(float(self._get_variable(param[1], param)) + 1), param)
        return self._return_empty()
    def dec(self, param: UniParam):
        if len(param.params) > 2:
            self._set_variable(param[1], float_to_str(float(self._get_variable(param[1], param)) - float(param[2])), param)
        elif len(param.params) == 2:
            self._set_variable(param[1], float_to_str(float(self._get_variable(param[1], param)) - 1), param)
        return self._return_empty()
    def cut(self, param: UniParam):
        if len(param[1]) == 0:
            param[1] = '0'
        if len(param[2]) == 0:
            param[2] = '0'
        start = int(param[1])
        end = int(param[2])
        if start < 0 and end < 0 and start > end:
            start, end = end, start
        string = param[3]
        return MacroResult(string[start:end])
    def header(self, param: UniParam):
        return MacroResult(param.request.headers.get(param[1], ''))
    def breadcrumbs(self, param: UniParam):
        t = param.interpreter.unquote(param[1], param, False).content
        r = []
        paths = param.request.path.split('/')[:-1]
        bread_url = ''
        bread_name = ''
        for i in range(len(paths)):
            bread_name = paths[i]
            bread_url += paths[i] + '/'
            symbols = concat_dict(param.symbols, {
                'bread-name': lambda p: MacroResult(bread_name),
                'bread-url': lambda p: MacroResult(bread_url)
            })
            param.symbols = concat_dict(param.symbols, symbols)
            c = param.interpreter.parse_text(t, param)
            r.append(c.content)
        return MacroResult(''.join(r))
    def time(self, param: UniParam):
        optional_params = self._get_optional_params(param, 'format', 'when')
        time_format = optional_params.get('format', 'yyyy-mm-dd hh:MM:ss')
        when = float(optional_params.get('when', time.time()))
        f = datetime.datetime.fromtimestamp(when)
        result = time_format.replace('c', str(f)).replace('yyyy', '%04d' % f.year).replace('mm', '%02d' % f.month).replace('dd', '%02d' % f.day).replace('hh', '%02d' % f.hour).replace('MM', '%02d' % f.minute).replace('ss', '%02d' % f.second)
        return MacroResult(result)
    def macro_if(self, param: UniParam):
        param.params.append('')
        return param.interpreter.unquote(param[2] if self._judge(param[1]) else param[3], param)
    def macro_if_not(self, param: UniParam):
        param.params.append('')
        return param.interpreter.unquote(param[3] if self._judge(param[1]) else param[2], param)
    def macro_not(self, param: UniParam):
        return MacroResult(self._bool(not self._judge(param[1])))
    def macro_break(self, param: UniParam):
        return MacroResult('', do_break=True)
    def comment(self, param: UniParam):
        return self._return_empty()
    def replace(self, param: UniParam):
        p = param.params
        string = p[-1]
        for i in range(1, len(p) - 1, 2):
            string = string.replace(p[i], param.interpreter.unquote(p[i + 1], param, True).content)
        return MacroResult(string)
    def section(self, param: UniParam):
        page = param.interpreter.get_section(param[1], param, True, True)
        return MacroResult(page.content, headers=page.headers)
    def translation(self, param: UniParam):
        t = param.interpreter
        p = param.params
        return MacroResult(t.translations[p[1]] if p[1] in t.translations else (p[2] if len(p) > 2 else p[1]))
    def equal(self, param: UniParam):
        p = param.params
        status = True
        for i in range(1, len(p) - 1):
            first: str = p[i]
            second: str = p[i + 1]
            if is_number(first) and is_number(second):
                first = float_to_str(float(first))
                second = float_to_str(float(second))
            if first != second:
                status = False
        return MacroResult(self._bool(status))
    def not_equal(self, param: UniParam):
        p = param.params
        status = True
        for i in range(1, len(p) - 1):
            first: str = p[i]
            second: str = p[i + 1]
            if is_number(first) and is_number(second):
                first = float_to_str(float(first))
                second = float_to_str(float(second))
            if first == second:
                status = False
        return MacroResult(self._bool(status))
    def greater_than(self, param: UniParam):
        p = param.params
        status = True
        for i in range(1, len(p) - 1):
            if float(p[i]) <= float(p[i + 1]):
                status = False
        return MacroResult(self._bool(status))
    def lesser_than(self, param: UniParam):
        p = param.params
        status = True
        for i in range(1, len(p) - 1):
            if float(p[i]) >= float(p[i + 1]):
                status = False
        return MacroResult(self._bool(status))
    def greater_or_equal_than(self, param: UniParam):
        p = param.params
        status = True
        for i in range(1, len(p) - 1):
            if float(p[i]) < float(p[i + 1]):
                status = False
        return MacroResult(self._bool(status))
    def lesser_or_equal_than(self, param: UniParam):
        p = param.params
        status = True
        for i in range(1, len(p) - 1):
            if float(p[i]) > float(p[i + 1]):
                status = False
        return MacroResult(self._bool(status))
    def disconnect(self, param: UniParam):
        return MacroResult('', disconnect=True)
    def add_header(self, param: UniParam):
        header = param[1].split(':')
        header_dict = { header[0]: header[1].strip() }
        return MacroResult('', headers=header_dict)
    def length(self, param: UniParam):
        return MacroResult(str(len(param[1])))
    def get(self, param: UniParam):
        # TODO
        key = param[1]
        result = self.FALSE
        if key in ('can recur', 'can archive', 'stop spiders'):
            result = self.TRUE
        elif key in ('can access'):
            account_name = param.statistics.accounts.get(param.request.cookies.get('HFS_SID_', ''), ('', ''))
            result = self._bool(Account.can_access(account_name, param.request.path_real, True))
        elif key in ('can delete'):
            account_name = param.statistics.accounts.get(param.request.cookies.get('HFS_SID_', ''), ('', ''))
            result = self._bool(Account.can_access(account_name, param.request.path_real, False))
        elif key == 'can upload':
            result = self._bool(if_upload_allowed_in(param.request.path_real, Config))
        elif key == 'accounts':
            result = Config.accounts.replace('|', ';')
        elif key == 'protocolon':
            result = 'https://' if param.request.is_secure else 'http://'
        elif key == 'speed limit':
            result = '0'
        elif key == 'agent':
            result = str(param.request.user_agent.browser)  # Maybe None, also differ from oHFS
        return MacroResult(result)
    def match(self, param: UniParam):
        regex = wildcard2re(param[1])
        result = re.match(regex, param[2], re.I | re.M)
        return MacroResult(self._bool(result))
    def regexp(self, param: UniParam):
        regex = param[1]
        result = re.match(regex, param[2], re.I | re.M)
        return MacroResult(self._bool(result))
    def macro_switch(self, param: UniParam):
        key = param[1]
        splitter = param[2]
        conditions = {}
        _current = ''
        for i, j in enumerate(param[3:-1]):
            if i % 2 == 0:
                _current = j
            else:
                for k in _current.split(splitter):
                    conditions[k] = j
        default = param[-1]
        return param.interpreter.unquote(conditions.get(key, default), param, True)
