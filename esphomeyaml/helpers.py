from __future__ import print_function

import errno
import logging
import os
import socket
import subprocess

from esphomeyaml.py_compat import text_type, IS_PY2

_LOGGER = logging.getLogger(__name__)


def ensure_unique_string(preferred_string, current_strings):
    test_string = preferred_string
    current_strings_set = set(current_strings)

    tries = 1

    while test_string in current_strings_set:
        tries += 1
        test_string = u"{}_{}".format(preferred_string, tries)

    return test_string


def indent_all_but_first_and_last(text, padding=u'  '):
    lines = text.splitlines(True)
    if len(lines) <= 2:
        return text
    return lines[0] + u''.join(padding + line for line in lines[1:-1]) + lines[-1]


def indent_list(text, padding=u'  '):
    return [padding + line for line in text.splitlines()]


def indent(text, padding=u'  '):
    return u'\n'.join(indent_list(text, padding))


# From https://stackoverflow.com/a/14945195/8924614
def cpp_string_escape(string, encoding='utf-8'):
    if isinstance(string, text_type):
        string = string.encode(encoding)
    result = ''
    for character in string:
        if IS_PY2:
            character = ord(character)
        if not (32 <= character < 127) or character in ('\\', '"'):
            result += '\\%03o' % character
        else:
            result += chr(character)
    return '"' + result + '"'


def color(the_color, message=''):
    from colorlog.escape_codes import escape_codes, parse_colors

    if not message:
        res = parse_colors(the_color)
    else:
        res = parse_colors(the_color) + message + escape_codes['reset']

    return res


def run_system_command(*args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    rc = p.returncode
    return rc, stdout, stderr


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def is_ip_address(host):
    parts = host.split('.')
    if len(parts) != 4:
        return False
    try:
        for p in parts:
            int(p)
        return True
    except ValueError:
        return False


def resolve_ip_address(host):
    try:
        ip = socket.gethostbyname(host)
    except socket.error as err:
        from esphomeyaml.core import EsphomeyamlError

        raise EsphomeyamlError("Error resolving IP address: {}".format(err))

    return ip
