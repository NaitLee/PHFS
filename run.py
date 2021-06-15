#!/usr/bin/python3
import os
os.chdir(os.path.dirname(__file__) or '.')

from cfgLib import Config
from serverLib import PHFSServer
from wsgiserver import WSGIServer

if __name__ == '__main__':
    server = WSGIServer(PHFSServer(), Config.host or ('0.0.0.0' if not Config.ipv6 else '::'), int(Config.port))
    server.start()
