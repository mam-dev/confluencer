# -*- coding: utf-8 -*-
# pylint: disable=wildcard-import, unused-wildcard-import, bad-continuation
""" Project automation for Invoke.
"""
# Copyright ©  2015 1&1 Group <git@1and1.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import, unicode_literals

import os
import shutil
import tempfile

from rituals.easy import *  # pylint: disable=redefined-builtin


@task(name='fresh-cookies',
    help={
        'mold': "git URL or directory to use for the refresh",
    },
)
def fresh_cookies(ctx, mold=''):
    """Refresh the project from the original cookiecutter template."""
    mold = mold or "https://github.com/Springerle/py-generic-project.git"  # TODO: URL from config
    tmpdir = os.path.join(tempfile.gettempdir(), "cc-upgrade-confluencer")

    if os.path.isdir('.git'):
        # TODO: Ensure there are no local unstashed changes
        pass

    # Make a copy of the new mold version
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    if os.path.exists(mold):
        shutil.copytree(mold, tmpdir, ignore=shutil.ignore_patterns(
            ".git", ".svn", "*~",
        ))
    else:
        ctx.run("git clone {} {}".format(mold, tmpdir))

    # Copy recorded "cookiecutter.json" into mold
    shutil.copy2("project.d/cookiecutter.json", tmpdir)

    with pushd('..'):
        ctx.run("cookiecutter --no-input {}".format(tmpdir))
    if os.path.exists('.git'):
        ctx.run("git status")

namespace.add_task(fresh_cookies)


@task(help={
    'pty': "Whether to run commands under a pseudo-tty",
})  # pylint: disable=invalid-name
def ci(ctx):
    """Perform continuous integration tasks."""
    opts = ['']

    # 'tox' makes no sense in Travis
    if os.environ.get('TRAVIS', '').lower() == 'true':
        opts += ['test.pytest']
    else:
        opts += ['test.tox']

    ctx.run("invoke --echo --pty clean --all build --docs check --reports{}".format(' '.join(opts)))

namespace.add_task(ci)
