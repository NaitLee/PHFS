
import hashlib

class PasswordToBaseHash():
    def __init__(self, password_plain: str):
        self._base_hash = hashlib.sha256(password_plain.encode('utf-8')).hexdigest().lower()
    def get(self):
        return self._base_hash

class BaseHashToTokenHash():
    def __init__(self, base_hash: str, token: str):
        self._token_hash = hashlib.sha256((base_hash + token).encode('utf-8')).hexdigest().lower()
    def get(self):
        return self._token_hash
