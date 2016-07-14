import hashlib
import binascii
from collections import OrderedDict

from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.translation import ugettext as _


class LegacyPasswordHasher(BasePasswordHasher):
    """ Legacy password hasher.
    Single SHA512 iteration with a 32 bytes salt.
    It's wrong and should not be used except for backward compatibility.
    CCVPN2 had it in a binary form, it must be base64-encoded and appened
    to "legacy_sha512$" during the migration.
    """
    algorithm = "legacy_sha512"

    def encode(self, password, salt):
        assert password is not None
        if isinstance(password, str):
            password = bytes(password, 'utf-8')
        if isinstance(salt, str):
            salt = bytes(salt, 'utf-8')
        hash = hashlib.sha512(salt + password)
        return "%s$%s%s" % (self.algorithm, binascii.b2a_hex(salt).decode('utf-8'),
                            hash.hexdigest())

    def verify(self, password, encoded):
        algorithm, rest = encoded.split('$', 1)
        assert algorithm == self.algorithm

        binary = binascii.a2b_hex(rest)

        encoded_2 = self.encode(password, binary[:32])
        return encoded == encoded_2

    def safe_summary(self, encoded):
        algorithm, hash = encoded.split('$', 1)
        assert algorithm == self.algorithm
        return OrderedDict([
            (_('algorithm'), algorithm),
            (_('salt'), hash[0:8]),
            (_('hash'), hash[64:72]),
        ])

    def must_update(self, encoded):
        return True  # "legacy"

