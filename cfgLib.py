
import os

from helpersLib import read_ini

class DictAsObject(dict):
    """ As this in classesLib.py, used for resolving circular importing.
    """
    def __init__(self, **kwargs):
        super().__init__(kwargs)
    def __getattr__(self, key):
        return self.get(key, None)
    def __setattr__(self, key, value):
        self[key] = value
        return


class ConfigManager(DictAsObject):
    def __init__(self, cfg_path='hfs.ini'):
        # I store my own development-use cfg in folder "~override"
        override_cfg_path = '~override/' + cfg_path
        self.cfg_path = override_cfg_path if os.path.exists(override_cfg_path) else cfg_path
        self['server'] = 'PHFS'
        self['version'] = '2.4.0 RC7'
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

Config = ConfigManager()

class AccountManager(DictAsObject):
    def __init__(self, cfg=Config):
        """ Reads accounts from `Config`
        """
        self.accounts = {
            '': ('', [cfg.base_path])
        }
        account_names = [x for x in cfg.accounts.split('|')]
        account_hashes = [x for x in cfg.passwords.split('|')]
        account_permitted = [[y for y in x.split('\\')] for x in cfg.account_permitted.split('|')]
        for i, j, k in zip(account_names, account_hashes, account_permitted):
            self.accounts[i] = (j, k)
    def get_account_detail(self, account_name: str) -> tuple:
        if account_name not in self.accounts:
            account_name = ''
        detail = self.accounts[account_name]
        return detail
    def can_access(self, account_name: str, path: str, guest_allowed=True) -> bool:
        status = (account_name != '') if guest_allowed else False
        for i in self.get_account_detail(account_name)[1]:
            if path.startswith(i):
                status = True
                break
        for i in self.accounts:
            if i == account_name or i == '':
                continue
            for j in self.accounts[i][1]:
                if path.startswith(j):
                    status = False
                    break
        return status

Account = AccountManager()
