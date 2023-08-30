# -*- coding: utf-8 -*-

#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this file. If not, see <http://www.gnu.org/licenses/>.
#
#   Copyright © 2014-2020 The University of Tromsø & the Norwegian Sámi Parliament
#   http://giellatekno.uit.no & http://divvun.no
#
"""Utility functions and classes used by other modules in CorpusTools."""

from __future__ import absolute_import, print_function, unicode_literals

import inspect
import operator
import os
import platform
import sys
from collections import namedtuple
from contextlib import contextmanager

import six

from six.moves import range

PathComponents = namedtuple('PathComponents',
                            'root module lang genre subdirs basename')


class SetupError(Exception):
    """This exception is raised when setup is faulty."""

    pass


class ExecutableMissingError(Exception):
    """This exception is raised when wanted executables are missing."""

    pass


class ArgumentError(Exception):
    """This exception is raised when argument errors occur."""

    pass


class ConversionError(Exception):
    """Raise this exception when conversions error occur."""

    pass


def print_frame(debug='', *args):
    """Print debug output."""
    # 0 represents this line, 1 represents line at caller
    callerframerecord = inspect.stack()[1]
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)

    print(info.lineno, info.function, debug, file=sys.stderr, end=' ')
    for arg in args:
        print(arg, file=sys.stderr, end=' ')
    print(file=sys.stderr)


def basename_noext(fname, ext):
    """Get the basename without the extension.

    Args:
        fname (str): path to the file.
        ext (str): the extension that should be removed.

    Returns:
        str: fname without the extension.
    """
    return os.path.basename(fname)[:-len(ext)]


def sort_by_value(table, **kwargs):
    """Sort the table by value.

    Args:
        table (dict): the dictionary that should be sorted.
        **kwargs: Keyword arguments passed on to the sorted function.

    Returns:
        dict: sorted by value.
    """
    return sorted(six.iteritems(table), key=operator.itemgetter(1), **kwargs)


def replace_all(replacements, string):
    """Replace unwanted strings with wanted strings.

    Args:
        replacements (list of tuple): unwanted:wanted string pairs.
        string (str): the string where replacements should be done.

    Returns:
        str: string with replaced strings.
    """
    for unwanted, wanted in replacements:
        string = string.replace(unwanted, wanted)

    return string


def split_path(path):
    """Split an absolute path into useful components.

    Args:
        path (str): a path to a file

    Returns:
        PathComponents namedtuple
    """

    def split_on_module(p):
        for module in [
                u"goldstandard/orig", u"prestable/converted",
                u"prestable/toktmx", u"prestable/tmx", u"orig", u"converted",
                u"stable", u"analysed"
        ]:
            d = u"/" + module + u"/"
            if d in p:
                root, rest = p.split(d)
                return root, module, rest

    # Ensure we have at least one / before module, for safer splitting:
    abspath = os.path.normpath(os.path.abspath(path))
    root, module, lang_etc = split_on_module(abspath)
    lang_list = lang_etc.split("/")
    lang, genre, subdirs, basename = lang_list[0], lang_list[1], lang_list[2:-1], lang_list[-1]

    return PathComponents(root, module, lang, genre, "/".join(subdirs),
                          basename)


def is_executable(fullpath):
    """Check if the program in fullpath is executable.

    Args:
        fullpath (str): the path to the program or script.

    Returns:
        bool: True if fullpath contains a executable, False otherwise.
    """
    return os.path.isfile(fullpath) and os.access(fullpath, os.X_OK)


def path_possibilities(program):
    """Check if program is found in $PATH.

    Args:
        program: name of program of script.

    Yields:
        possible fullpath to the program
    """
    return (os.path.join(path.strip('"'), program)
            for path in os.environ["PATH"].split(os.pathsep))


def executable_in_path(program):
    """Check if program is in path.

    Args:
        program (str): name of the program

    Returns:
        bool: True if program is found, False otherwise.
    """
    fpath, _ = os.path.split(program)
    if fpath:
        return is_executable(program)
    else:
        return any(
            is_executable(possible_path)
            for possible_path in path_possibilities(program))


def sanity_check(program_list):
    """Look for programs and files that are needed to do the analysis.

    If they don't exist, raise an exception.
    """
    if 'GTHOME' not in os.environ:
        raise SetupError("You have to set the environment variable GTHOME "
                         "to your checkout of langtech/trunk!")
    for program in program_list:
        if executable_in_path(program) is False:
            raise ExecutableMissingError(
                'Please install {}, can not continue without it.'.format(program))


def get_lang_resource(lang, resource, fallback=None):
    """Get a language resource.

    Args:
        lang (str): the language of the resource.
        resource (str): the resource that is needed.
        fallback (str or None): the fallback resource. Default is None.

    Returns:
        str: path to the resource or fallback.
    """
    path = os.path.join(os.environ['GTHOME'], 'langs', lang, resource)
    if os.path.exists(path):
        return path
    else:
        return fallback


def get_preprocess_command(lang):
    """Get the complete proprocess command for lang.

    Args:
        lang (str): the language

    Returns:
        str: the complete preprocess command.
    """
    preprocess_script = os.path.join(os.environ['GTHOME'],
                                     'gt/script/preprocess')
    sanity_check([preprocess_script])
    abbr_fb = get_lang_resource("sme", 'tools/preprocess/abbr.txt')
    abbr = get_lang_resource(lang, 'tools/preprocess/abbr.txt', abbr_fb)
    return [preprocess_script, "--abbr={}".format(abbr)]


def lineno():
    """Return the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno


def print_element(element, level, indent, out):
    """Format an html document.

    This function formats html documents for readability, to see
    the structure of the given document. It ruins white space in
    text parts.

    Args:
        element (etree._Element): the element to format.
        level (int): indicate at what level this element is.
        indent (int): indicate how many spaces this element should be indented
        out (stream): a buffer where the formatted element is written.
    """
    tag = element.tag.replace('{http://www.w3.org/1999/xhtml}', '')

    out.write(' ' * (level * indent))
    out.write('<{}'.format(tag))

    for k, v in six.iteritems(element.attrib):
        out.write(' ')
        if isinstance(k, six.text_type):
            out.write(k)
        else:
            out.write(k)
        out.write('="')
        if isinstance(v, six.text_type):
            out.write(v)
        else:
            out.write(v)
        out.write('"')
    out.write('>\n')

    if element.text is not None and element.text.strip() != '':
        out.write(' ' * ((level + 1) * indent))
        out.write(element.text.strip())
        out.write('\n')

    for child in element:
        print_element(child, level + 1, indent, out)

    out.write(' ' * (level * indent))
    out.write('</{}>\n'.format(tag))

    if level > 0 and element.tail is not None and element.tail.strip() != '':
        for _ in range(0, (level - 1) * indent):
            out.write(' ')
        out.write(element.tail.strip())
        out.write('\n')


def name_to_unicode(filename):
    """Turn a filename to a unicode string.

    Args:
        filename (str): name of the file

    Returns:
        A unicode string.
    """
    if platform.system() == 'Windows':
        return filename
    else:
        return filename.decode('utf-8')


def note(msg):
    """Print msg to stderr.

    Args:
        msg (str): the message
    """
    print(msg, file=sys.stderr)


@contextmanager
def ignored(*exceptions):
    """Ignore exceptions."""
    try:
        yield
    except exceptions:
        pass
