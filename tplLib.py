
from classesLib import TplSection, UniParam, MacroResult, MacroToCallable
from scriptLib import Commands
from helpersLib import replace_str, read_ini, object_from_dict

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
        self.sections = object_from_dict({
            '': TplSection('', ['public'], {})
        })
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
                plus = False
                prepend = False
                if j[0:1] == '+':
                    plus = True
                    j = j[1:]
                elif j[0:1] == '^':
                    prepend = True
                    j = j[1:]
                if j not in self.sections:
                    self.sections[j] = TplSection('', [], {})
                if plus:
                    self.sections[j].content += t[1]
                elif prepend:
                    self.sections[j].content = t[1] + self.sections[j].content
                else:
                    self.sections[j].content = t[1]
                    self.sections[j].params = p
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
                plus = False
                if j[0:1] == '+':
                    plus = True
                    j = j[1:]
                if j not in self.sections:
                    self.sections[j] = TplSection('', [], {})
                if plus:
                    self.sections[j].content += t[1]
                else:
                    self.sections[j].content = t[1]
                    self.sections[j].params = p
        self.translations = {}
        for i in self.sections['special:strings'].content.split('\n'):
            pair = i.split('=', 1)
            if len(pair) < 2:
                continue
            self.translations[pair[0]] = pair[1]
        alias_from_txt = read_ini('alias.txt')
        for i in alias_from_txt:
            self.handler[i] = MacroToCallable(alias_from_txt[i], self)
        for i in self.sections['special:alias'].content.split('\n'):
            pair = i.split('=', 1)
            if len(pair) < 2:
                continue
            self.handler[pair[0]] = MacroToCallable(pair[1], self)
        return
    def parse_text(self, text: str, param: UniParam) -> MacroResult:
        """ Parse a string and apply symbols and macros
        """
        for i in param.symbols:
            if '%%%s%%' % i in text:
                text = text.replace('%%%s%%' % i, param.symbols[i](UniParam([i], symbols=param.symbols, interpreter=self)))
        macro_level = 0
        quote_level = 0
        position = 0
        newlines = 0
        last_newline_at = 0
        length = len(text)
        full_macro = ['']
        broken = False
        disconnect = False
        headers = {
            'Server': 'PHFS/0.0.1'
        }
        cookies = []
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
                                return MacroResult('', do_break=True, disconnect=True, headers=headers, cookies=cookies)
                            for i in result.headers:
                                headers[i] = result.headers[i]
                            for i in result.cookies:
                                cookies.append(i)
                        macro_str = '{.' + '|'.join(full_macro) + '.}'
                        text = replace_str(text, macro_str, result.content)
                        for i in param.symbols:
                            if '%%%s%%' % i in text:
                                text = text.replace('%%%s%%' % i, param.symbols[i](UniParam([i], symbols=param.symbols, interpreter=self)))
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
        return MacroResult(text, do_break=broken, disconnect=disconnect, headers=headers, cookies=cookies)
    def unquote(self, text: str, param: UniParam, do_parse=True) -> MacroResult:
        if text[0:2] == '{:' and text[-2:] == ':}':
            text = text[2:-2]
        return self.parse_text(text, param) if do_parse else MacroResult(text)
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
    def exec_macro(self, params: list, param: UniParam) -> MacroResult:
        params = self.to_normal_macro(params)
        result = self.handler[params[0]](UniParam(params, symbols=param.symbols, interpreter=self))
        return result
    