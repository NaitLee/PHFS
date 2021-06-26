
import os, io, tarfile, tempfile, mimeLib, time, re
from werkzeug.wrappers import Request, Response
from werkzeug.utils import send_file
from tplLib import Interpreter
from classesLib import UniParam, Page, FileList, ItemEntry
from cfgLib import Config
from helpersLib import get_dirname, if_upload_allowed_in, purify_filename, wildcard2re, join_path

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
    itp_filelist = interpreter
    if os.path.exists('hfs.filelist.tpl'):
        itp_filelist = Interpreter('hfs.filelist.tpl')
    else:
        itp_filelist = Interpreter('filelist.tpl')
    def __init__(self):
        pass
    def not_found_response(self, request: PTIRequest) -> Response:
        page = self.interpreter.get_page('error-page', UniParam(['not found', 404], interpreter=self.interpreter, request=request))
        return Response(page.content, page.status, page.headers)
    def wsgi(self, environ, start_response):
        request_initial = Request(environ)
        response = Response('bad request', 400)
        page = Page('', 400)
        path = request_initial.path
        resource = join_path(Config.base_path, path)
        request = PTIRequest(environ, path, resource)
        uni_param = UniParam([], interpreter=self.interpreter, request=request, filelist=FileList([]))
        levels_virtual = path.split('/')
        # levels_real = resource.split('/')
        if request.args.get('tpl', '') == 'list':
            uni_param.interpreter = self.itp_filelist
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
                        filename = purify_filename(single_file.filename)
                        try:
                            single_file.save(join_path(resource, filename))
                            upload_result[filename] = (True, '')
                        except Exception as e:
                            upload_result[filename] = (False, str(e))
                    page = self.interpreter.get_page('upload-results', UniParam([upload_result], interpreter=self.interpreter, request=request))
                    response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
                return response(environ, start_response)
        if 'mode' in request.args:
            # urlvar mode
            mode = request.args['mode']
            if mode == 'section':
                section_name = request.args.get('id', '')
                page = uni_param.interpreter.section_to_page(section_name, uni_param)
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
            path_real_dir = request.path_real_dir + '/'
            shown_files = [x for x in (items_folder + items_file) if x[0:1] != '.'] if Config.hide_dots else (items_folder + items_file)
            paths = [x.replace('\\', '/') for x in shown_files]
            items = [ItemEntry(x, x, path_real_dir) for x in paths]
            filelist = FileList(items)
            uni_param.filelist = filelist
            page = uni_param.interpreter.get_page('', uni_param)
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
            path_real_dir = request.path_real_dir + '/'
            shown_files = [x for x in (items_folder + items_file) if x[0:1] != '.'] if Config.hide_dots else (items_folder + items_file)
            paths = [x.replace('\\', '/') for x in shown_files]
            items = [ItemEntry(x, x, path_real_dir) for x in paths]
            filelist = FileList(items)
            uni_param.filelist = filelist
            page = uni_param.interpreter.get_page('', uni_param)
            response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
            return response(environ, start_response)
        elif levels_virtual[-1][0:1] == '~':
            # Command
            command = levels_virtual[-1][1:]
            if len(levels_virtual) == 2:
                # Section call, only at root
                section = uni_param.interpreter.get_section(command, uni_param, True, False)
                if section != None:
                    page = Page(section.content, 200)
                    response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime(path))
                else:
                    response = self.not_found_response(request)
            if command == 'upload' and if_upload_allowed_in(request.path_real, Config):
                page = uni_param.interpreter.get_page('upload', uni_param)
                response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
            elif command == 'folder.tar':
                tmp = tempfile.TemporaryFile(mode='w+b')
                tar = tarfile.open(mode='w', fileobj=tmp)
                path_real = request.path_real_dir + '/'
                shown_files = [x for x in os.listdir(request.path_real_dir) if x[0:1] != '.'] if Config.hide_dots else os.listdir(request.path_real_dir)
                for i in shown_files:
                    is_recursive = 'recursive' in request.args or bool(Config.recur_archive)
                    tar.add(path_real + i, i, recursive=is_recursive)
                tar.close()     # Pointer is at the end of file
                tmp.seek(0)     # Read at start
                response = send_file(tmp, environ, mimetype=mimeLib.getmime('*.tar'))
            elif command == 'files.lst':
                uni_param.interpreter = self.itp_filelist
                path_real_dir = request.path_real_dir + '/'
                shown_files = [x for x in os.listdir(request.path_real_dir) if x[0:1] != '.'] if Config.hide_dots else os.listdir(request.path_real_dir)
                paths = [join_path(path_real_dir, x) for x in shown_files]
                items = [ItemEntry(x, x, path_real_dir) for x in paths]
                filelist = FileList(items)
                uni_param.filelist = filelist
                page = uni_param.interpreter.get_page('', uni_param)
                response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.txt'))
            return response(environ, start_response)
        elif resource != None:
            # Filelist or send file or 404
            if os.path.exists(resource):
                if os.path.isdir(resource):
                    if 'no list' not in uni_param.interpreter.sections[''].params:
                        path_real_dir = request.path_real_dir + '/'
                        shown_files = [x for x in os.listdir(path_real_dir) if x[0:1] != '.'] if Config.hide_dots else os.listdir(path_real_dir)
                        paths = [join_path(path_real_dir, x) for x in shown_files]
                        items = [ItemEntry(x, x, path_real_dir) for x in paths]
                        filelist = FileList(items)
                        uni_param.filelist = filelist
                    page = uni_param.interpreter.get_page('', uni_param)
                    response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.txt' if uni_param.interpreter == self.itp_filelist else '*.html'))
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
