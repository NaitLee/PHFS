
import os

from helpersLib import read_ini
from classesLib import DictAsObject

class CFG(DictAsObject):
    def __init__(self, cfg_path='hfs.ini'):
        # I store my own development-use cfg in folder "~override"
        override_cfg_path = '~override/' + cfg_path
        self.cfg_path = override_cfg_path if os.path.exists(override_cfg_path) else cfg_path
        self['server'] = 'PHFS'
        self['version'] = '0.0.1'
        self['build'] = '001'
        d = read_ini(self.cfg_path)
        for i in d:
            self[i] = d[i]
    def write_ini(self):
        content = []
        for i in self:
            content.append('%s=%s\n' % (i, str(self[i])))
        f = open(self.cfg_path, 'w', encoding='utf-8')
        f.write(''.join(content))
        f.close()

Config = CFG()
