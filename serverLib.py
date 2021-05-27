
import os, io, mimeLib
from werkzeug.wrappers import Request, Response
from werkzeug.utils import send_file
from tplLib import Interpreter
from classesLib import UniParam, Page, PageParam

class PTIRequest(Request):
    path_virtual: str = '/'
    path_real: str = '/'
    def __init__(self, environ, path_virtual='/', path_real='/'):
        super().__init__(environ)
        self.path_virtual = path_virtual
        self.path_real = path_real

class PHFSServer():
    interpreter = Interpreter()
    def __init__(self):
        pass
    def not_found_response(self, request: PTIRequest) -> Response:
        page = self.interpreter.get_page('error-page', PageParam(['not found', 404], request))
        return Response(page.content, page.status, page.headers)
    def wsgi(self, environ, start_response):
        request_initial = Request(environ)
        response = Response('bad request', 400)
        page = Page('', 400)
        path = request_initial.path
        resource = path
        request = PTIRequest(environ, path, resource)
        if path[0:2] == '/~':
            section_name = path[2:]
            section = self.interpreter.get_section(section_name, UniParam([], interpreter=self.interpreter, request=request), True, False)
            if section == None:
                response = self.not_found_response(request)
            else:
                page = Page(section.content, 200)
                response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime(path))
        elif resource != None:
            if path[-1] == '/' and request.path_real[-1] == '/':
                page = self.interpreter.get_page('', UniParam([], interpreter=self.interpreter, request=request))
                response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
            else:
                if os.path.exists(request.path_real) and os.path.isfile(request.path_real):
                    response = send_file(request.path_real, environ)
                else:
                    response = self.not_found_response(request)
        else:
            response = self.not_found_response(request)
        return response(environ, start_response)
    def __call__(self, environ, start_response):
        return self.wsgi(environ, start_response)
