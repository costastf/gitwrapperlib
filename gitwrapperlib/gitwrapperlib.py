#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: gitwrapperlib.py
#
# Copyright 2018 Costas Tyfoxylos
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
#

"""
Main code for gitwrapperlib.

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""

import logging
import sys
import re
try:
    import sh
except ImportError:
    # fallback: emulate the sh API with pbs
    import pbs

    class Sh:  # pylint: disable=too-few-public-methods
        """
        Overloading pbs to look like sh.

        https://stackoverflow.com/questions/28618906/porting-sh-1-11-based-code-to-windows
        """

        def __getattr__(self, attr):
            return pbs.Command(attr)
    sh = Sh()
from .gitwrapperlibexceptions import ExecutableNotFound

__author__ = '''Costas Tyfoxylos <costas.tyf@gmail.com>'''
__docformat__ = '''google'''
__date__ = '''02-01-2018'''
__copyright__ = '''Copyright 2018, Costas Tyfoxylos'''
__credits__ = ["Costas Tyfoxylos"]
__license__ = '''MIT'''
__maintainer__ = '''Costas Tyfoxylos'''
__email__ = '''<costas.tyf@gmail.com>'''
__status__ = '''Development'''  # "Prototype", "Development", "Production".


# This is the main prefix used for logging
LOGGER_BASENAME = '''gitwrapperlib'''
LOGGER = logging.getLogger(LOGGER_BASENAME)
LOGGER.addHandler(logging.NullHandler())


class Git:
    """Models the git command and contstructs some extra helper methods."""

    passthrough_methods = ('init', 'pull')
    argument_methods = ('add', 'clone', 'push')

    def __init__(self):
        logger_name = u'{base}.{suffix}'.format(base=LOGGER_BASENAME,
                                                suffix=self.__class__.__name__)
        self._logger = logging.getLogger(logger_name)
        self._git = self._get_command()

    @staticmethod
    def _get_command():
        if sys.platform in ('win32', 'cygwin'):
            try:
                sh.git()
            except WindowsError:  # pylint: disable=undefined-variable
                raise ExecutableNotFound
            except pbs.ErrorReturnCode_1:
                git = sh.git
        else:
            try:
                git = sh.Command('git')
            except sh.CommandNotFound:
                raise ExecutableNotFound
        return git

    def __getattr__(self, name):  # pylint: disable=inconsistent-return-statements
        if name in self.passthrough_methods:
            return getattr(self._git, name)
        if name in self.argument_methods:
            def wrapper(*args, **kwargs):  # noqa
                return getattr(self._git, name)(*args, **kwargs)
            return wrapper

    def remove(self, path):
        """Removes a path with force."""
        self._git.rm('-rf', path)

    def add_forced(self, path):
        """Adds a path with force."""
        self._git.add('-f', path)

    def commit(self, message, *args):
        """Commits."""
        self._git.commit('-m', message, *args)

    def add_remote_origin(self, url):
        """Adds the remote origin."""
        self._git.remote('add', 'origin', url)

    def push_master(self):
        """Pushes to master."""
        self._git.push('origin', 'master')

    def push_force_master(self):
        """Pushes to master."""
        self._git.push('origin', 'master', '--force')

    def push_force_branch(self, branch):
        """Pushes to master."""
        self._git.push('origin', branch, '--force')

    def branch_upstream_to_master(self):
        """Branches upstream to master."""
        self._git.branch('-u', 'origin/master')

    def get_branches(self):
        """Returns a list of the branches."""
        return [self._sanitize(branch)
                for branch in self._git.branch(color="never").splitlines()]

    @staticmethod
    def _sanitize(value):
        if value.startswith('*'):
            value = value.split()[1]
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        value = ansi_escape.sub('', value.strip())
        return value

    def get_current_branch(self):
        """Returns the currently active branch."""
        return next((self._sanitize(branch)
                     for branch in self._git.branch(color="never").splitlines()
                     if branch.startswith('*')),
                    None)

    def create_branch(self, name):
        """Creates a branch."""
        self._git.branch(name)

    def remove_branch(self, name):
        """Removes a branch."""
        self._git.branch('-d', name)

    def switch_branch(self, name):
        """Switches to a branch."""
        self._git.checkout(name)

    def list_tags(self):
        """Lists existing tags."""
        return self._git.tag()

    def add_tag(self, value):
        """Tag with provided value."""
        self._git.tag(value)

    def delete_tag(self, value):
        """Delete the tag provided."""
        self._git.tag('-d', value)

    def create_patch(self, from_tag, to_tag):
        """Create a patch between tags."""
        return str(self._git.diff('{}..{}'.format(from_tag, to_tag), _tty_out=False))
