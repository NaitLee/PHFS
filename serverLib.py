
import os, io, tarfile, tempfile, mimeLib, time
from werkzeug.wrappers import Request, Response
from werkzeug.utils import send_file
from tplLib import Interpreter
from classesLib import UniParam, Page, PageParam
from cfgLib import Config
from helpersLib import get_dirname, if_upload_allowed_in, is_filename_illegal

class PTIRequest(Request):
    path_virtual: str = '/'
    path_real: str = '/'
    def __init__(self, environ, path_virtual='/', path_real='/'):
        super().__init__(environ)
        self.path_virtual = path_virtual
        self.path_real = path_real
        self.path_virtual_dir = get_dirname(path_virtual)
        self.path_real_dir = get_dirname(path_real)
        self.build_time_start = time.time()

class IllegalFilenameError(Exception):
    """ Filename is illegal
    """

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
        param = UniParam([], interpreter=self.interpreter, request=request)
        levels = path.split('/')
        if request.method == 'POST':
            # File upload
            if len(request.files) > 0:
                if not if_upload_allowed_in(request.path_real, Config):
                    response = Response('forbidden', 403)
                else:
                    upload_result = {}
                    for i in request.files:
                        single_file = request.files[i]
                        if single_file.filename == '':
                            continue
                        try:
                            if is_filename_illegal(single_file.filename):
                                raise IllegalFilenameError('Illegal filename')
                            single_file.save(resource + single_file.filename)
                            upload_result[single_file.filename] = (True, '')
                        except Exception as e:
                            upload_result[single_file.filename] = (False, str(e))
                    page = self.interpreter.get_page('upload-results', PageParam([upload_result], request))
                    response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
                return response(environ, start_response)
        if 'mode' in request.args:
            # urlvar mode
            mode = request.args['mode']
            if mode == 'section':
                section_name = request.args.get('id', '')
                page = self.interpreter.section_to_page(section_name, param)
                response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime(section_name))
            return response(environ, start_response)
        elif path[0:2] == '/~':
            # Section, ~ at root
            section_name = path[2:]
            section = self.interpreter.get_section(section_name, param, True, False)
            if section == None:
                response = self.not_found_response(request)
            else:
                page = Page(section.content, 200)
                response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime(path))
            return response(environ, start_response)
        elif levels[-1][0:1] == '~':
            # Command
            command = levels[-1][1:]
            if command == 'upload' and if_upload_allowed_in(request.path_real, Config):
                page = self.interpreter.get_page('upload', param)
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
            else:
                response = self.not_found_response(request)
            return response(environ, start_response)
        elif resource != None:
            # Filelist or send file or 404
            if os.path.exists(resource):
                if os.path.isdir(resource):
                    page = self.interpreter.get_page('', param)
                    response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
                else:
                    response = send_file(resource, environ)
            else:
                response = self.not_found_response(request)
            return response(environ, start_response)
        else:
            response = self.not_found_response(request)
        return response(environ, start_response)
    def __call__(self, environ, start_response):
        return self.wsgi(environ, start_response)
