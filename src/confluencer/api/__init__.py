# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation
""" Confluence API support.
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
from __future__ import absolute_import, unicode_literals, print_function

import os
import sys
import logging
from contextlib import contextmanager

import requests
from bunch import bunchify
from rudiments.reamed import click

from .. import __version__ as version


ERRORS = (
    requests.RequestException,
)


@contextmanager
def context(*args, **kwargs):
    """Context manager providing an API object with standard error logging."""
    api = ConfluenceAPI(*args, **kwargs)
    try:
        yield api
    except ERRORS as cause:
        api.log.error("API ERROR: %s", cause)
        raise


class ConfluenceAPI(object):
    """ Support for using the Confluence API.

        Since the Confluence API has excellent support for discovery by
        e.g. the ``_links`` attribute in results, this just adds a thin
        convenience layer above plain ``requests`` HTTP calls.
    """

    def __init__(self, endpoint=None):
        self.log = logging.getLogger('cfapi')
        self.base_url = endpoint or os.environ.get('CONFLUENCE_BASE_URL')
        assert self.base_url, "You MUST set the CONFLUENCE_BASE_URL environment variable!"
        self.base_url = self.base_url.rstrip('/')

        # Enable HTTP logging when 'requests' logger is on DEBUG level
        if logging.getLogger("requests").getEffectiveLevel() <= logging.DEBUG:
            try:
                import http.client as http_client
            except ImportError:  # Python 2
                import httplib as http_client
            http_client.HTTPConnection.debuglevel = 1

        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'Confluencer/{} [{}]'.format(version, requests.utils.default_user_agent())

    def url(self, path):
        """Build an API URL from partial paths."""
        url = path
        if not url.startswith('/rest/api/') and '://' not in url:
            url = '/rest/api/' + url.lstrip('/')
        if not url.startswith('http'):
            url = self.base_url + url
        return url

    def get(self, path, **params):
        """GET an API path and return bunchified result."""
        url = self.url(path)
        self.log.debug("GET from %r", url)
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return bunchify(response.json())

    def getall(self, path, **params):
        """ Yield all results of a paginated GET.

            If the ``limit`` keyword argument is set, it is used to stop the
            generator after the given number of result items.

            :param path: Confluence API URI.
            :param params: Request parameters.
        """
        params = params.copy()
        pos, outer_limit = 0, params.pop('limit', sys.maxint)
        while path:
            response = self.get(path, **params)
            for item in response.get('results', []):
                pos += 1
                if pos > outer_limit:
                    return
                yield item

            path = response.get('_links', {}).get('next', None)
            params.clear()
