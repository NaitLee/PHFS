
import os, io, tarfile, tempfile, mimeLib, time
from werkzeug.wrappers import Request, Response
from werkzeug.utils import send_file
from tplLib import Interpreter
from classesLib import UniParam, Page, PageParam
from cfgLib import Config

class PTIRequest(Request):
    path_virtual: str = '/'
    path_real: str = '/'
    def __init__(self, environ, path_virtual='/', path_real='/'):
        super().__init__(environ)
        self.path_virtual = path_virtual
        self.path_real = path_real
        self.path_virtual_dir = os.path.dirname(path_virtual)
        self.path_real_dir = os.path.dirname(path_real)
        self.build_time_start = time.time()
        

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
        resource = Config.base_path + path
        request = PTIRequest(environ, path, resource)
        if request.method == 'GET':
            levels = path.split('/')
            if path[0:2] == '/~':
                # Section, ~ at root
                section_name = path[2:]
                section = self.interpreter.get_section(section_name, UniParam([], interpreter=self.interpreter, request=request), True, False)
                if section == None:
                    response = self.not_found_response(request)
                else:
                    page = Page(section.content, 200)
                    response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime(path))
            elif levels[-1][0:1] == '~':
                # Command
                command = levels[-1][1:]
                if command == 'upload':
                    page = self.interpreter.get_page('upload', UniParam([], interpreter=self.interpreter, request=request))
                    response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
                elif command == 'folder.tar':
                    tmp = tempfile.TemporaryFile(mode='w+b')
                    tar = tarfile.open(mode='w', fileobj=tmp)
                    path_real = '/'.join(levels[0:-1]) + '/'
                    for i in os.listdir(path_real):
                        is_recursive = True # 'recursive' in request.args
                        tar.add(path_real + i, i, recursive=is_recursive)
                    tar.close()     # Pointer is at the end of file
                    tmp.seek(0)     # Read at start
                    response = send_file(tmp, environ, mimetype=mimeLib.getmime('*.tar'))
            elif resource != None:
                if os.path.exists(resource):
                    if os.path.isdir(resource):
                        page = self.interpreter.get_page('', UniParam([], interpreter=self.interpreter, request=request))
                        response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
                    else:
                        response = send_file(resource, environ)
                else:
                    response = self.not_found_response(request)
            else:
                response = self.not_found_response(request)
        elif request.method == 'POST':
            upload_result = {}
            for i in request.files:
                single_file = request.files[i]
                try:
                    single_file.save(resource + single_file.filename)
                    upload_result[single_file.filename] = (True, '')
                except Exception as e:
                    upload_result[single_file.filename] = (False, str(e))
            page = self.interpreter.get_page('upload-result', PageParam([upload_result], request))
            response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
        return response(environ, start_response)
    def __call__(self, environ, start_response):
        return self.wsgi(environ, start_response)
