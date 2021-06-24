#!/usr/bin/python3
import os
os.chdir(os.path.dirname(__file__) or '.')

from cfgLib import Config

from serverLib import PHFSServer
from werkzeug.serving import run_simple

if __name__ == '__main__':
    run_simple(Config.host, int(Config.port), PHFSServer(), use_reloader=True, use_debugger=True, threaded=True, extra_files=['hfs.tpl', 'hfs.filelist.tpl', 'hfs.ini'])
