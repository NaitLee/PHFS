
import locale

from cfgLib import Config
from helpersLib import parse_ini

class I18nManager():
    _default_locale = Config.locale or locale.getlocale()[0]
    i18n = {
        'en-US': {}
    }
    def __init__(self):
        f = open('i18n.ini', 'r', encoding='utf-8')
        raw_content = '\n' + f.read()
        f.close()
        for i in raw_content.split('\n[')[1:]:
            j, k = i.split(']\n')
            self.i18n[j] = parse_ini(k)
    def get_locale(self) -> tuple:
        return locale.getlocale()
    def get_string(self, key_str: str, locale=_default_locale) -> str:
        return self.i18n.get(locale, self.i18n['en-US']).get(key_str, key_str)

I18n = I18nManager()
