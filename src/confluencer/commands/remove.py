# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation, too-few-public-methods
""" 'rm' command.
"""
# Copyright ©  2015 – 2017 1&1 Group <git@1and1.com>
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
from __future__ import absolute_import, unicode_literals, print_function

import sys

from munch import Munch as Bunch
from rudiments.reamed import click

from .. import config, api
from ..tools import content


@config.cli.group(name='rm')
@click.pass_context
def remove(ctx):
    """Remove contents."""


@remove.command()
@click.argument('pages', metavar='‹page-url›…', nargs=-1)
@click.pass_context
def tree(ctx, pages):
    """Remove page(s) including their descendants."""
    # TODO: implement me
    with api.context() as cf:
        try:
            response = None
        except api.ERRORS as cause:
            # Just log and otherwise ignore any errors
            api.diagnostics(cause)
        else:
            pass
