
from typing import Union

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

class PageParam():
    """ Params for getting a page with `Interpreter.get_page`
    """
    params: list
    request = None
    def __init__(self, params: list, request):
        self.params = params
        self.request = request

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
        `params`: A `list` of params, used by macros.  
        `symbols`: A `dict` with callable values, used by interpreter.  
        `interpreter`: A `TplInterpreter` instance.  
        `request`: The WSGI request.
    """
    params: list
    symbols: dict = {}
    interpreter = None
    request = None
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
