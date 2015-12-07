# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


import re

from swh.core.hashutil import ALGORITHMS, hex_to_hash
from swh.web.ui.exc import BadInputExc


SHA256_RE = re.compile(r'^[0-9a-f]{64}$', re.IGNORECASE)
SHA1_RE = re.compile(r'^[0-9a-f]{40}$', re.IGNORECASE)


def parse_hash(q):
    """Detect the hash type of a user submitted query string.

    Args:
        query string with the following format: "[HASH_TYPE:]HEX_CHECKSUM",
        where HASH_TYPE is optional, defaults to "sha1", and can be one of
        swh.core.hashutil.ALGORITHMS

    Returns:
        A pair (hash_algorithm, byte hash value)

    Raises:
        ValueError if the given query string does not correspond to a valid
        hash value

    """
    def guess_algo(q):
        if SHA1_RE.match(q):
            return 'sha1'
        elif SHA256_RE.match(q):
            return 'sha256'
        else:
            raise BadInputExc('Invalid checksum query string %s' % q)

    def check_algo(algo, hex):
        if (algo in {'sha1', 'sha1_git'} and not SHA1_RE.match(hex)) \
           or (algo == 'sha256' and not SHA256_RE.match(hex)):
            raise BadInputExc('Invalid hash %s for algorithm %s' % (hex, algo))

    parts = q.split(':')
    if len(parts) > 2:
        raise BadInputExc('Invalid checksum query string %s' % q)
    elif len(parts) == 1:
        parts = (guess_algo(q), q)
    elif len(parts) == 2:
        check_algo(parts[0], parts[1])

    algo = parts[0]
    if algo not in ALGORITHMS:
        raise BadInputExc('Unknown hash algorithm %s' % algo)

    return (algo, hex_to_hash(parts[1]))
