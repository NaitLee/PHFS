from wsgiref.handlers import CGIHandler
from serverLib import PHFSServer

try:
    CGIHandler().run(PHFSServer())
except KeyboardInterrupt:
    pass
