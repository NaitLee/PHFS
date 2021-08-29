
import os, io, tarfile, tempfile, mimeLib, time, re, random, hashlib, zipfile, datetime, time, shutil
import hashLib
from werkzeug.wrappers import Request, Response
from werkzeug.utils import send_file
from tplLib import Interpreter
from classesLib import UniParam, Page, FileList, ItemEntry, ZipItemEntry
from cfgLib import Config, Account
from helpersLib import get_dirname, if_upload_allowed_in, purify_filename, wildcard2re, join_path, year_letter_from_number, smartremove
from i18nLib import I18n

builtin_sections = ('sha256.js')

class PHFSRequest(Request):
    # Session variables for macro execution
    variables = {}
    # For {.count.}, values will be int
    counts = {}
    # For {.from table.} and {.set table.}, there will be nested tables
    table = {}
    def __init__(self, environ, path_virtual='/', path_real='/'):
        super().__init__(environ)
        self.path_virtual = path_virtual
        self.path_real = path_real
        self.path_virtual_dir = get_dirname(path_virtual)
        self.path_real_dir = get_dirname(path_real)
        self.build_time_start = time.time()

class PHFSStatistics():
    # Listing completed? for {.after the list.}
    listing_completed = False
    # Accounts are saved as a dict, key is sid and value is tuple (username, IP)
    accounts = {}
    # Global variables for macro execution
    variables = {}

class PHFSServer():
    indexes = ('index.html', 'index.htm', 'default.html', 'default.htm')
    request: PHFSRequest
    statistics = PHFSStatistics()
    interpreter = Interpreter()
    itp_filelist = interpreter
    if os.path.exists('hfs.filelist.tpl'):
        itp_filelist = Interpreter('hfs.filelist.tpl')
    else:
        itp_filelist = Interpreter('filelist.tpl')
    cached_zip_files = {}
    def __init__(self):
        pass
    def log_request(self, h='0.0.0.0', l='-', u='-', t='[01/01/0001:00:00:00 +0000]', m='GET', U='/', q='', H='HTTP/1.1', s=200, b=0):
        print(
            Config.log_format
                .replace('%h', h)
                .replace('%l', l)
                .replace('%u', u or '-')
                .replace('%t', t)
                .replace('%r', '%m %U%q %H')
                .replace('%m', m)
                .replace('%U', U)
                .replace('%q', ('?' + q) if q else '')
                .replace('%H', H or 'HTTP/1.1')
                .replace('%s', str(s))
                .replace('%>s', str(s))
                .replace('%b', str(b))
        )
    def log_message(self, message: str):
        print(message)
    def not_found_response(self, request: PHFSRequest) -> Response:
        page = self.interpreter.get_page('error-page', UniParam(['not found', 404], interpreter=self.interpreter, request=request, statistics=self.statistics))
        return Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
    def unauth_response(self, request: PHFSRequest) -> Response:
        page = self.interpreter.get_page('error-page', UniParam(['unauthorized', 403], interpreter=self.interpreter, request=request, statistics=self.statistics))
        return Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
    def get_current_account(self, request: PHFSRequest) -> tuple:
        return self.statistics.accounts.get(request.cookies.get('HFS_SID_', ''), ('', ''))
    def return_response(self, request: PHFSRequest, response: Response, environ, start_response):
        if 'Location' in response.headers:
            response.status_code = 302
        if 'HFS_SID_' not in request.cookies:
            sid = hashlib.sha256(bytes([random.randint(0, 255) for _ in range(32)])).hexdigest()
            response.headers['Set-Cookie'] = 'HFS_SID_=%s; HttpOnly' % sid
        account_name = self.get_current_account(request)[0]
        current_time = datetime.datetime.now()
        current_timezone = current_time.astimezone().tzinfo.utcoffset(None).seconds / 60 / 60
        formatted_time = '[%s/%s/%s:%s:%s:%s %s]' % (
            '%02i' % current_time.day,
            year_letter_from_number(current_time.month),
            '%04i' % current_time.year,
            '%02i' % current_time.hour,
            '%02i' % current_time.minute,
            '%02i' % current_time.second,
            ('-' if current_timezone < 0 else '+') + ('%04i' % abs(current_timezone * 100))
        )
        self.log_request(
            request.remote_addr,
            '-',
            account_name,
            formatted_time,
            request.method,
            request.path,
            request.query_string.decode('utf-8'),
            '',
            response.status_code,
            response.content_length
        )
        return response(environ, start_response)
    def wsgi(self, environ, start_response):
        request_initial = Request(environ)
        request_initial.path = request_initial.path.replace('/..', '')
        response = Response('bad request', 400)
        page = Page('', 400)
        path = request_initial.path
        resource = join_path(Config.base_path, path)
        request = PHFSRequest(environ, path, resource)
        self.request = request
        if os.path.isdir(resource):
            # If there's a index.html inside folder, show that
            for i in self.indexes:
                if os.path.isfile(join_path(resource, i)):
                    path = join_path(path, i)
                    resource = join_path(resource, i)
        uni_param = UniParam([], interpreter=self.interpreter, request=request, filelist=FileList([]), statistics=self.statistics)
        levels_virtual = path.split('/')
        levels_real = resource.split('/')
        if resource[-1:] != '/' and os.path.isdir(resource):
            response = Response('', 302, {'Location': path + '/'})
            return self.return_response(request, response, environ, start_response)
        if not Account.can_access(self.get_current_account(request)[0], resource, True):
            response = self.unauth_response(request)
            return self.return_response(request, response, environ, start_response)
        if request.args.get('tpl', '') == 'list':
            uni_param.interpreter = self.itp_filelist
        if request.method == 'POST':
            if len(request.files) > 0:
                # File upload
                if not if_upload_allowed_in(request.path_real, Config):
                    response = Response('forbidden', 403)
                else:
                    upload_result = {}
                    for i in request.files:
                        single_file = request.files[i]
                        filename = purify_filename(single_file.filename)
                        if filename == '':
                            continue
                        elif filename in self.indexes:
                            upload_result[filename] = (False, I18n.get_string('file_name_or_extension_forbidden'))
                            continue
                        try:
                            single_file.save(join_path(resource, filename))
                            upload_result[filename] = (True, '')
                        except Exception as e:
                            upload_result[filename] = (False, str(e))
                    page = self.interpreter.get_page('upload-results', UniParam([upload_result], interpreter=self.interpreter, request=request, statistics=self.statistics))
                    response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.html'))
                return self.return_response(request, response, environ, start_response)
            if request.form.get('action', '') == 'delete':
                if not Account.can_access(self.get_current_account(request)[0], resource, False):
                    response = Response('forbidden', 403)
                else:
                    filelist = request.form.getlist('selection')
                    try:
                        for i in filelist:
                            smartremove(Config.base_path + i)
                        response = Response('ok', 200)
                    except Exception as err:
                        response = Response(str(err), 500)
                return self.return_response(request, response, environ, start_response)
        if 'mode' in request.args:
            # urlvar mode
            mode = request.args['mode']
            if mode == 'section':
                section_name = request.args.get('id', '')
                page = uni_param.interpreter.section_to_page(section_name, uni_param)
                response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime(section_name))
            elif mode == 'login':
                account_name = request.form.get('user')
                token_hash = request.form.get('passwordSHA256')
                expected_hash = hashLib.BaseHashToTokenHash(Account.get_account_detail(account_name)[0], request.cookies.get('HFS_SID_', '')).get()
                if account_name not in Account.accounts:
                    response = Response('username not found', 200)
                elif token_hash != expected_hash:
                    response = Response('bad password', 200)
                else:
                    sid = hashlib.sha256(bytes([random.randint(0, 255) for _ in range(32)])).hexdigest()
                    self.statistics.accounts[sid] = (account_name, request.host)
                    response = Response('ok', 200)
                    response.headers.add_header('Set-Cookie', 'HFS_SID_=%s; HttpOnly; Max-Age=0' % request.cookies.get('HFS_SID_', ''))
                    response.headers.add_header('Set-Cookie', 'HFS_SID_=%s; HttpOnly' % sid)
            elif mode == 'logout':
                sid = request.cookies.get('HFS_SID_', '')
                if sid in self.statistics.accounts:
                    del self.statistics.accounts[sid]
                response = Response('ok', 200, {'Set-Cookie': 'HFS_SID_=%s; HttpOnly; Max-Age=0' % sid})
            elif mode == 'archive':
                tmp = tempfile.TemporaryFile(mode='w+b')
                tar = tarfile.open(mode='w', fileobj=tmp)
                path_real = request.path_real_dir + '/'
                filelist = request.form.getlist('selection')
                final_list_without_dots = [((Config.base_path if x[0:1] == '/' else path_real) + x) for x in filelist if x[0:1] != '.']
                final_list_with_dots = [((Config.base_path if x[0:1] == '/' else path_real) + x) for x in filelist]
                shown_files = final_list_without_dots if Config.hide_dots else final_list_with_dots
                for i in shown_files:
                    is_recursive = 'recursive' in request.args or bool(Config.recur_archive)
                    tar.add(i, i, recursive=is_recursive)
                tar.close()     # Pointer is at the end of file
                tmp.seek(0)     # Read at start
                response = send_file(tmp, environ, mimetype=mimeLib.getmime('*.tar'), as_attachment=True, download_name=os.path.basename(request.path_virtual_dir) + '.selection.tar')
            return self.return_response(request, response, environ, start_response)
        elif 'search' in request.args:
            # Search, with re.findall
            directory = request.path_real_dir
            if not os.path.isdir(directory):
                response = self.not_found_response(request)
                return self.return_response(request, response, environ, start_response)
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
            return self.return_response(request, response, environ, start_response)
        elif 'filter' in request.args:
            # Filter, with re.fullmatch
            directory = request.path_real_dir
            if not os.path.isdir(directory):
                response = self.not_found_response(request)
                return self.return_response(request, response, environ, start_response)
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
            return self.return_response(request, response, environ, start_response)
        elif levels_virtual[-1][0:1] == '~':
            # Command
            command = levels_virtual[-1][1:]
            if len(levels_virtual) == 2:
                # Section call, only at root
                global builtin_sections
                section = uni_param.interpreter.get_section(command, uni_param, True, False)
                if section != None:
                    page = Page(section.content, 200)
                    response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime(path))
                elif command in builtin_sections:
                    response = send_file(command, environ, mimeLib.getmime(command))
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
            return self.return_response(request, response, environ, start_response)
        elif resource != None:
            # Filelist or send file or 404
            if os.path.exists(resource):
                if os.path.isdir(resource):
                    # List files
                    if 'no list' not in uni_param.interpreter.sections[''].params:
                        path_real_dir = request.path_real_dir + '/'
                        shown_files = [x for x in os.listdir(path_real_dir) if x[0:1] != '.'] if Config.hide_dots else os.listdir(path_real_dir)
                        paths = [join_path(path_real_dir, x) for x in shown_files]
                        items = [ItemEntry(x, x, path_real_dir) for x in paths]
                        filelist = FileList(items)
                        uni_param.filelist = filelist
                    page = uni_param.interpreter.get_page('', uni_param)
                    response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.txt' if uni_param.interpreter == self.itp_filelist else '*.html'))
                elif levels_real[-1].lower().endswith('.zip') and Config.preview_zip:
                    # Preview zip file if configured
                    if resource not in self.cached_zip_files:
                        try:
                            zip_file = zipfile.ZipFile(resource, 'r')
                        except zipfile.BadZipFile:
                            response = Response(I18n.get_string('zip_file_is_broken'), 202)
                            return self.return_response(request, response, environ, start_response)
                        self.cached_zip_files[resource] = (zip_file, )
                    zip_file_data = self.cached_zip_files[resource]
                    if 'getitem' in request.args:
                        zip_file = zip_file_data[0]
                        filename = request.args['getitem']
                        try:
                            response = Response(zip_file.read(filename), 200, mimetype=mimeLib.getmime(filename))
                        except KeyError:
                            response = self.not_found_response(request)
                    else:
                        items = [ZipItemEntry(x, resource, path) for x in zip_file_data[0].filelist if x.filename[-1:] != '/']
                        filelist = FileList(items)
                        uni_param.filelist = filelist
                        page = uni_param.interpreter.get_page('', uni_param)
                        response = Response(page.content, page.status, page.headers, mimetype=mimeLib.getmime('*.txt' if uni_param.interpreter == self.itp_filelist else '*.html'))
                else:
                    # A file
                    response = send_file(resource, environ)
            else:
                # 404
                response = self.not_found_response(request)
            return self.return_response(request, response, environ, start_response)
        else:
            response = self.not_found_response(request)
        return self.return_response(request, response, environ, start_response)
    def __call__(self, environ, start_response):
        return self.wsgi(environ, start_response)
