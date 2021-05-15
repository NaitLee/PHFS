
class Page():
    def __init__(self, content, status=400, headers={}, cookies=[]):
        self.content = content
        self.status = status
        self.headers = headers
        self.cookies = cookies

class MacroResult():
    def __init__(self, content: str, break_exec=False, headers={}, cookies=[]):
        self.content = content
        self.break_exec = break_exec
        self.headers = headers
        self.cookies = cookies

class MacroParams():
    def __init__(self, params: list, tpl_interpreter=None, symbols={}, request=None, vfs_manager=None, settings_manager=None):
        self.params = params
        self.tpl_interpreter = tpl_interpreter
        self.symbols = symbols
        self.request = request
        self.vfs_manager = vfs_manager
        self.settings_manager = settings_manager

class MacroToCallable():
    def __init__(self, macro_str: str, tpl_interpreter):
        if not (macro_str[0:2] == '{.' and macro_str[-2:] == '.}'):
            macro_str = '{.' + macro_str + '.}'
        self.macro_str = macro_str
        self.tpl_interpreter = tpl_interpreter
    def __call__(self, param: MacroParams) -> MacroResult:
        new_str = self.macro_str    # Prevent changing original string
        for i, j in enumerate(param.params):
            new_str = new_str.replace('$' + str(i), j)
        return self.tpl_interpreter.parse_text(new_str, param.symbols, param)
