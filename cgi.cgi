#!/usr/bin/python3

from wsgiref.handlers import CGIHandler
from serverLib import PHFSServer

CGIHandler().run(PHFSServer())
