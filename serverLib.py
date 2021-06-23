
import os, io, tarfile, tempfile, mimeLib, time, re
from werkzeug.wrappers import Request, Response
from werkzeug.utils import send_file
from tplLib import Interpreter
from classesLib import UniParam, Page, PageParam
from cfgLib import Config
from helpersLib import get_dirname, if_upload_allowed_in, is_filename_illegal, wildcard2re

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
    """ Upload: Filename is illegal
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
        uni_param = UniParam([], interpreter=self.interpreter, request=request)
        page_param = PageParam([], request)
        levels_virtual = path.split('/')
        # levels_real = resource.split('/')
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
                page = self.interpreter.section_to_page(section_name, page_param)
                response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime(section_name))
            return response(environ, start_response)
        elif 'search' in request.args:
            # Search, with re.findall
            directory = request.path_real_dir
            if not os.path.isdir(directory):
                response = self.not_found_response(request)
                return response(environ, start_response)
            pattern = re.compile(wildcard2re(request.args['search']), re.I)
            recursive = 'recursive' in request.args or bool(Config.recur_search)
            items_folder = []
            items_file = []
            if recursive:
                for dirpath, dirnames, filenames in os.walk(directory):
                    for i in dirnames:
                        if re.findall(pattern, i):
                            items_folder.append(os.path.join(dirpath, i))
                    for i in filenames:
                        if re.findall(pattern, i):
                            items_file.append(os.path.join(dirpath, i))
            else:
                for i in os.scandir(directory):
                    if re.findall(pattern, i.name):
                        if i.is_dir:
                            items_folder.append(i.path)
                        else:
                            items_file.append(i.path)
            page = self.interpreter.get_page('', PageParam([items_folder + items_file, True], request))
            response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
            return response(environ, start_response)
        elif 'filter' in request.args:
            # Filter, with re.fullmatch
            directory = request.path_real_dir
            if not os.path.isdir(directory):
                response = self.not_found_response(request)
                return response(environ, start_response)
            pattern = re.compile(wildcard2re(request.args['filter']), re.I)
            recursive = 'recursive' in request.args or bool(Config.recur_search)
            items_folder = []
            items_file = []
            if recursive:
                for dirpath, dirnames, filenames in os.walk(directory):
                    for i in dirnames:
                        if re.fullmatch(pattern, i):
                            items_folder.append(os.path.join(dirpath, i))
                    for i in filenames:
                        if re.fullmatch(pattern, i):
                            items_file.append(os.path.join(dirpath, i))
            else:
                for i in os.scandir(directory):
                    if re.fullmatch(pattern, i.name):
                        if i.is_dir:
                            items_folder.append(i.path)
                        else:
                            items_file.append(i.path)
            page = self.interpreter.get_page('', PageParam([items_folder + items_file, True], request))
            response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
            return response(environ, start_response)
        elif levels_virtual[-1][0:1] == '~':
            # Command
            command = levels_virtual[-1][1:]
            if len(levels_virtual) == 2:
                # Section call, only at root
                section = self.interpreter.get_section(command, uni_param, True, False)
                if section != None:
                    page = Page(section.content, 200)
                    response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime(path))
                else:
                    response = self.not_found_response(request)
            if command == 'upload' and if_upload_allowed_in(request.path_real, Config):
                page = self.interpreter.get_page('upload', page_param)
                response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
            elif command == 'folder.tar':
                tmp = tempfile.TemporaryFile(mode='w+b')
                tar = tarfile.open(mode='w', fileobj=tmp)
                path_real = request.path_real_dir + '/'
                for i in os.listdir(path_real):
                    is_recursive = 'recursive' in request.args or bool(Config.recur_archive)
                    tar.add(path_real + i, i, recursive=is_recursive)
                tar.close()     # Pointer is at the end of file
                tmp.seek(0)     # Read at start
                response = send_file(tmp, environ, mimetype=mimeLib.getmime('*.tar'))
            return response(environ, start_response)
        elif resource != None:
            # Filelist or send file or 404
            if os.path.exists(resource):
                if os.path.isdir(resource):
                    page = self.interpreter.get_page('', page_param)
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
