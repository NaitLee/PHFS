
import os, io, mimeLib
from werkzeug.wrappers import Request, Response
from werkzeug.utils import send_file
from tplLib import TplInterpreter
from vfsLib import VFSManager
from classesLib import MacroParams, Page

class PHFSServer(TplInterpreter):
    def __init__(self):
        super().__init__()
        self.vfs_manager = VFSManager()
    def wsgi(self, environ, start_response):
        request = Request(environ)
        response = Response('bad request', 400)
        page = Page('', 400, False, {}, [])
        path = request.path
        resource = self.vfs_manager.url_to_resource(path)
        if path[0:2] == '/~':
            section = path[2:]
            page = self.get_section(section, MacroParams([], self, {}, request, self.vfs_manager), True, False)
            response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime(path))
        else:
            if path[-1] == '/' and resource[-1] == '/':
                page = self.get_section('', MacroParams([], self, {}, request, self.vfs_manager), True, True)
                response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime(path))
            else:
                if os.path.exists(resource) and os.path.isfile(resource):
                    response = send_file(resource, environ)
                else:
                    page = self.get_section('not found', MacroParams([], self, {}, request, self.vfs_manager), True, True)
                    response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
        if page.disconnect:
            return Response()(environ, start_response)
        return response(environ, start_response)
    def __call__(self, environ, start_response):
        return self.wsgi(environ, start_response)
