#!/usr/bin/python3
import os, sys, tempfile, shutil
os.chdir(os.path.dirname(__file__) or '.')

from helpersLib import smartcopy
from cfgLib import Config, Account
from i18nLib import I18n

if __name__ == '__main__':
    print(I18n.get_string('starting_server'))

if len(sys.argv) > 1:
    if len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg.isdigit():
            Config.port = arg
        else:
            if os.path.exists(arg):
                arg = os.path.abspath(arg).replace('\\', '/')
                if os.path.isdir(arg):
                    Config.base_path = arg
                    Account.accounts[''] = ('', arg)
                    print(I18n.get_string('base_path_set_to_0').format(arg))
                elif os.path.isfile(arg):
                    tempdir = tempfile.mkdtemp()
                    smartcopy(arg, tempdir)
                    Config.base_path = tempdir
                    Account.accounts[''] = ('', tempdir)
                    print(I18n.get_string('base_path_set_to_0_which_includes_copy_of_all_selected_files').format(tempdir))
    else:
        tempdir = tempfile.mkdtemp()
        for i in sys.argv[1:]:
            if os.path.exists(i):
                smartcopy(os.path.abspath(i), tempdir)
        Config.base_path = tempdir
        Account.accounts[''] = ('', tempdir)
        print(I18n.get_string('base_path_set_to_0_which_includes_copy_of_all_selected_files').format(tempdir))

from serverLib import PHFSServer
from wsgiserver import WSGIServer

if __name__ == '__main__':
    print(I18n.get_string('running_at_port_0').format(Config.port))
    server = WSGIServer(PHFSServer(), Config.host, int(Config.port))
    server.start()
