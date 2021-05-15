#!/usr/bin/python3
import os

os.chdir(os.path.dirname(__file__) or '.')

from serverLib import PHFSServer
from werkzeug.serving import run_simple

if __name__ == '__main__':
    run_simple('', 8090, PHFSServer(), use_reloader=True, use_debugger=True, threaded=True)