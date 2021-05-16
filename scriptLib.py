
from classesLib import MacroResult, MacroParams
from helpers import concat_dict, wildcard2re
import datetime, time, re

class StandardCommands():
    TRUE = '1'
    FALSE = ''
    FALSE_VALUES = ('', '0')
    class VarContainer():
        def __init__(self):
            self.vars = {}
        def __setitem__(self, key, value):
            self.vars[key] = value
        def __getitem__(self, key):
            return self.vars[key] if key in self.vars else ''
    def __init__(self):
        self.global_vars = {}
    def _judge(self, value):
        return False if value.strip() in self.FALSE_VALUES else True
    def _bool(self, value):
        return self.TRUE if value else self.FALSE
    def sym_style(self, param: MacroParams):
        return param.tpl_interpreter.get_section('style', param, True, True)
    def sym_user(self, param: MacroParams):
        return MacroResult('')
    def breadcrumbs(self, param: MacroParams):
        t = param.tpl_interpreter.unquote(param.params[1], param.symbols, param, False).content
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
            c = param.tpl_interpreter.parse_text(t, symbols, param)
            r.append(c.content)
        return MacroResult(''.join(r))
    def time(self, param: MacroParams):
        format_ = 'yyyy-mm-dd hh:MM:ss'
        when = 0
        result = ''
        for i in param.params:
            if i.startswith('format='):
                format_ = i[7:]
            if i.startswith('when='):
                when = float(i[5:])
        if when == 0:
            when = time.time()
        f = datetime.datetime.fromtimestamp(when)
        result = format_.replace('yyyy', '%04d' % f.year).replace('yy', '%02d' % f.year).replace('mm', '%02d' % f.month).replace('dd', '%02d' % f.day).replace('hh', '%02d' % f.hour).replace('MM', '%02d' % f.minute).replace('ss', '%02d' % f.second)
        return MacroResult(result)
    def macro_if(self, param: MacroParams):
        param.params.append('')
        return param.tpl_interpreter.unquote(param.params[2] if self._judge(param.params[1]) else param.params[3], param.symbols, param)
    def macro_if_not(self, param: MacroParams):
        param.params.append('')
        return param.tpl_interpreter.unquote(param.params[3] if self._judge(param.params[1]) else param.params[2], param.symbols, param)
    def macro_not(self, param: MacroParams):
        return MacroResult(self._bool(not self._judge(param.params[1])))
    def macro_break(self, param: MacroParams):
        return MacroResult('', True)
    def comment(self, param: MacroParams):
        return MacroResult('')
    def replace(self, param: MacroParams):
        p = param.params
        string = p[-1]
        for i in range(1, len(p) - 1, 2):
            string = string.replace(p[i], p[i + 1])
        return MacroResult(string)
    def section(self, param: MacroParams):
        page = param.tpl_interpreter.get_section(param.params[1], param, True, True)
        return MacroResult(page.content, False, False, page.headers, page.cookies)
    def translation(self, param: MacroParams):
        t = param.tpl_interpreter
        p = param.params
        return MacroResult(t.translations[p[1]] if p[1] in t.translations else (p[2] if len(p) > 2 else p[1]))
    def equal(self, param: MacroParams):
        p = param.params
        status = True
        for i in range(1, len(p) - 1):
            if p[i] != p[i + 1]:
                status = False
        return MacroResult(self._bool(status))
    def not_equal(self, param: MacroParams):
        p = param.params
        status = True
        for i in range(1, len(p) - 1):
            if p[i] == p[i + 1]:
                status = False
        return MacroResult(self._bool(status))
    def disconnect(self, param: MacroParams):
        return MacroResult('', True, True)
    def add_header(self, param: MacroParams):
        header = param.params[1].split(':')
        header_dict = { header[0]: header[1].strip() }
        return MacroResult('', False, False, header_dict)
    def length(self, param: MacroParams):
        return MacroResult(str(len(param.params[1])))
    def get(self, param: MacroParams):
        # TODO
        return MacroResult(self.FALSE)
    def match(self, param: MacroParams):
        regex = wildcard2re(param.params[1])
        result = re.match(regex, param.params[2], re.I | re.M)
        return MacroResult(self._bool(result))
class CommandsMap(StandardCommands):
    def __init__(self):
        self.commands_map = {
            'sym_style': self.sym_style,
            'sym_user': self.sym_user,
            'if': self.macro_if,
            'if not': self.macro_if_not,
            'not': self.macro_not,
            'breadcrumbs': self.breadcrumbs,
            'break': self.macro_break,
            'replace': self.replace,
            'translation': self.translation,
            'section': self.section,
            'comment': self.comment,
            '=': self.equal,
            '!=': self.not_equal,
            '<>': self.not_equal,
            'disconnect': self.disconnect,
            'add header': self.add_header,
            'time': self.time,
            'length': self.length,
            'get': self.get,
            'match': self.match,
            '_unsupported': lambda param: MacroResult(','.join(param.params))
        }