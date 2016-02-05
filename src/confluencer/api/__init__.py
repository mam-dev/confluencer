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
import re
import sys
import json
import base64
import struct
import logging
from contextlib import contextmanager

import requests
from bunch import bunchify
from rudiments.reamed import click

from .. import __version__ as version
from .._compat import text_type, urlparse, urlunparse, parse_qs, urlencode, unquote_plus


# Exceptions that API calls typically emit
ERRORS = (
    requests.RequestException,
)


def page_id_from_tiny_link(uri, _re=re.compile(r'/x/([-_A-Za-z0-9]+)')):
    """ Extract the page ID from a so-called *tiny link*.

        See `this answer <https://answers.atlassian.com/questions/87971/what-is-the-algorithm-used-to-create-the-tiny-links>`
        for details.
    """
    matched = _re.search(uri)
    if matched:
        tiny_url_id = matched.group(1)
        if isinstance(tiny_url_id, text_type):
            tiny_url_id = tiny_url_id.encode('ascii')
        page_id_bytes = (base64.urlsafe_b64decode(tiny_url_id) + b'\0\0\0\0')[:4]
        return struct.unpack('<L', page_id_bytes)[0]
    else:
        raise ValueError("Not a tiny link: {}".format(uri))


def tiny_id(page_id):
    """Return *tiny link* ID for the given page ID."""
    return base64.urlsafe_b64encode(struct.pack('<L', int(page_id)).rstrip(b'\0')).rstrip(b'=').decode('ascii')


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
                import httplib as http_client  # pylint: disable=import-error
            http_client.HTTPConnection.debuglevel = 1

        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'Confluencer/{} [{}]'.format(version, requests.utils.default_user_agent())

    def url(self, path):
        """ Build an API URL from partial paths.

            Parameters:
                path (str): Page URL / URI in various formats (tiny, title, id).

            Yields:
                str: The fully qualified API URL for the page.

            Raises:
                ValueError: A ``path`` was passed that isn't understood, or malformed.
        """
        url = path

        # Fully qualify partial URLs
        if not url.startswith('/rest/api/') and '://' not in url:
            url = '/rest/api/' + url.lstrip('/')
        if not url.startswith('http'):
            url = self.base_url + url

        if '/rest/api/' not in url:
            # Parse and rewrite URLs of the following forms:
            #   https://confluence.example.com/pages/viewpage.action?pageId=#######
            #   https://confluence.example.com/display/SPACEKEY/Page+Title
            #   https://confluence.example.com/x/TTTTT
            scheme, netloc, url_path, params, query, fragment = urlparse(url)
            query = parse_qs(query or '')
            #print((scheme, netloc, url_path, params, query, fragment))

            if url_path.endswith('/pages/viewpage.action'):
                # Page link with ID
                page_id = int(query.pop('pageId', [0])[0])
                if page_id:
                    url_path = '{}/rest/api/content/{}'.format(url_path.split('/pages/')[0], page_id)
                else:
                    raise ValueError("Missing 'pageId' in malformed URL '{}'".format(path))
            elif 'display' in url_path.lstrip('/').split('/')[:2]:
                # Page link with title
                matched = re.search(r'/display/([^/]+)/([^/]+)', url_path)
                if matched:
                    url_path = '{}/rest/api/content/search'.format(url_path.split('/display/')[0])
                    title = unquote_plus(matched.group(2))
                    search_query = dict(
                        cql='title="{}"'.format(title.replace('"', '?')),
                        cqlcontext=json.dumps(dict(spaceKey=matched.group(1))),
                    )
                    search_url = urlunparse((scheme, netloc, url_path, params, urlencode(search_query), fragment))
                    found = self.get(search_url)
                    if found.size == 1:
                        url_path, url = None, found.results[0]._links.self
                    else:
                        raise ValueError("{} results while searching for page with URL '{}', query was:\n{}"
                                         .format('Multiple' if found.size else 'No', path, search_url))
                else:
                    raise ValueError("Missing '.../display/SPACE/TITLE' in malformed URL '{}'".format(path))
            elif 'x' in url_path.lstrip('/').split('/')[:2]:
                # Tiny link
                page_id = page_id_from_tiny_link(url_path)
                url_path = '{}/rest/api/content/{}'.format(url_path.split('/x/')[0], page_id)
            else:
                raise ValueError("Cannot create API endpoint from malformed URL '{}'".format(path))

            if url_path:
                url = urlunparse((scheme, netloc, url_path, params, urlencode(query), fragment))

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
        pos, outer_limit = 0, params.pop('limit', sys.maxsize)
        while path:
            response = self.get(path, **params)
            for item in response.get('results', []):
                pos += 1
                if pos > outer_limit:
                    return
                yield item

            path = response.get('_links', {}).get('next', None)
            params.clear()
