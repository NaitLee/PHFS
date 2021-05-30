#!/usr/bin/python3
import os
from cfgLib import Config

os.chdir(os.path.dirname(__file__) or '.')

from serverLib import PHFSServer
from werkzeug.serving import run_simple

if __name__ == '__main__':
    run_simple(Config.host, int(Config.port), PHFSServer(), use_reloader=True, use_debugger=True, threaded=True, extra_files=['hfs.tpl', 'hfs.ini'])
