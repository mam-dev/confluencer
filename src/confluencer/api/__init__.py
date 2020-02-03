# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation, protected-access, no-else-return
""" Confluence API support.

    https://developer.atlassian.com/cloud/confluence/rest/
"""
# Copyright ©  2015-2018 1&1 Group <git@1and1.com>
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
import collections
from contextlib import contextmanager

import requests
import requests_cache
from addict import Dict as AttrDict
from rudiments.reamed import click

from .. import config
from .. import __version__ as version
from .._compat import text_type, urlparse, urlunparse, parse_qs, urlencode, unquote_plus


# Exceptions that API calls typically emit
ERRORS = (
    requests.RequestException,
)
MAX_ERROR_LINES = 15


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
        #tiny_url_id += b'=' * (len(tiny_url_id) % 4)
        page_id_bytes = (base64.b64decode(tiny_url_id, altchars=b'_-') + b'\0\0\0\0')[:4]
        return struct.unpack('<L', page_id_bytes)[0]
    else:
        raise ValueError("Not a tiny link: {}".format(uri))


def tiny_id(page_id):
    """Return *tiny link* ID for the given page ID."""
    return base64.b64encode(struct.pack('<L', int(page_id)).rstrip(b'\0'), altchars=b'_-').rstrip(b'=').decode('ascii')


def diagnostics(cause):
    """Display diagnostic info based on the given cause."""
    import pprint

    if not cause:
        return

    response = getattr(cause, 'response', None)
    request = getattr(response, 'request', None)
    # pprint.pprint(vars(response))
    # pprint.pprint(vars(request))

    method = 'HTTP {}'.format(request.method) if request else 'HTTP'
    try:
        data = pprint.pformat(response.json(), indent=4)
    except (AttributeError, TypeError, ValueError):
        try:
            data = response.content
        except AttributeError:
            data = ''
    if data:
        data = data.splitlines()
        if len(data) > MAX_ERROR_LINES:
            data = data[:MAX_ERROR_LINES] + ['...']
        data = '| RESPONSE BODY:\n' + '\n'.join(['|   ' + x for x in data])

    click.serror("{} ERROR: {}".format(method, cause))
    if data:
        click.secho(data)


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

    CACHE_EXPIRATION = 10 * 60 * 60  # seconds
    UA_NAME = 'Confluencer'

    def __init__(self, endpoint=None, session=None):
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

        self.session = session or requests.Session()
        self.session.headers['User-Agent'] = '{}/{} [{}]'.format(
            self.UA_NAME, version, requests.utils.default_user_agent())

        self.cached_session = requests_cache.CachedSession(
            cache_name=config.cache_file(type(self).__name__),
            expire_after=self.CACHE_EXPIRATION)
        self.cached_session.headers['User-Agent'] = self.session.headers['User-Agent']

    def url(self, path):
        """ Build an API URL from partial paths.

            Parameters:
                path (str): Page URL / URI in various formats (tiny, title, id).

            Returns:
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
                        # CF 3.5.x ignores cqlcontext?
                        cql='title="{}" AND space="{}"'.format(
                            title.replace('"', '?'), matched.group(1)
                        ),
                        cqlcontext=json.dumps(dict(spaceKey=matched.group(1))),
                    )
                    search_url = urlunparse((scheme, netloc, url_path, params, urlencode(search_query), fragment))
                    found = self.get(search_url)
                    if found.size == 1:
                        url_path, url = None, found.results[0]._links.self
                    else:
                        raise ValueError("{} results while searching for page with URL '{}'{}, query was:\n{}"
                                         .format('Multiple' if found.size else 'No',
                                                 path,
                                                 '' if found.size else ' (maybe indexing is lagging)',
                                                 search_url))
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
        """ GET an API path and return result.

            If ``_cached=True`` is provided, the cached session is used.
        """
        params = params.copy()
        cached = params.pop('_cached', False)
        url = self.url(path)
        self.log.debug("GET from %r", url)
        response = (self.cached_session if cached else self.session).get(url, params=params)
        response.raise_for_status()
        result = AttrDict(response.json())
        result._info.server = response.headers.get('Server', '')
        result._info.sen = response.headers.get('X-ASEN', '')
        return result

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
            #import pprint; print('\nGETALL RESPONSE'); pprint.pprint(response); print('')
            if 'page' in params.get('expand', '').split(','):
                response = response['page']
            items = response.get('results', [])
            for item in items:
                pos += 1
                if pos > outer_limit:
                    return
                yield item

            path = response.get('_links', {}).get('next', None)
            params.clear()

    def add_page(self, space_key, title, body, parent_id=None, labels=None):
        """ Create a new page.

            The body must be in 'storage' representation.
        """
        data = {
            "type": "page",
            "title": title,
            "space": {
                "key": space_key,
            },
            "body": {
                "storage": {
                    "value": body,
                    "representation": "storage",
                }
            }
        }
        if parent_id:
            data.update(dict(ancestors=[dict(type='page', id=parent_id)]))

        url = self.url('/content')
        self.log.debug("POST (add page) to %r", url)
        response = self.session.post(url, json=data)
        response.raise_for_status()
        page = AttrDict(response.json())
        self.log.debug("Create '%s': %r", title, response)

        # Add any provided labels
        if labels:
            data = [dict(prefix='global', name=label) for label in labels]
            response = self.session.post(page._links.self + '/label', json=data)
            response.raise_for_status()
            self.log.debug("Labels for #'%s': %r %r",
                           page.id, response, [i['name'] for i in response.json()['results']])

        return page

    def update_page(self, page, body, minor_edit=True):
        """ Update an existing page.

            The page **MUST** have been retrieved using ``expand='body.storage,version,ancestors'``.
        """
        if page.body.storage.value == body:
            self.log.debug("Update: Unchanged page '%s', doing nothing", page.title)
        else:
            data = {
                "id": page.id,
                "type": page.type,
                "title": page.title,
                "space": {
                    "key": page._expandable.space.split('/')[-1],
                },
                "body": {
                    "storage": {
                        "value": body,
                        "representation": "storage",
                    }
                },
                "version": {"number": page.version.number + 1, "minorEdit": minor_edit},
                "ancestors": [{'type': page.ancestors[-1].type, 'id': page.ancestors[-1].id}],
            }

            url = self.url('/content/{}'.format(page.id))
            self.log.debug("PUT (update page) to %r", url)
            #import pprint; print('\nPAGE UPDATE'); pprint.pprint(data); print('')
            response = self.session.put(url, json=data)
            response.raise_for_status()
            page = AttrDict(response.json())
            self.log.debug("Create '%s': %r", page.title, response)

        return page

    def delete_page(self, page, status=None):
        """ Delete an existing page.

            To permanently purge trashed content, pass ``status='trashed'``.
        """
        url = self.url('/content/{}'.format(page.id))
        self.log.debug("DELETE %r (status=%r)", url, status)
        data = {}
        if status:
            data['status'] = status
        response = self.session.delete(url, json=data)
        response.raise_for_status()

    def user(self, username=None, key=None):
        """ Return user details.

            Passing neither user name nor key retrieves the current user.
        """
        if key:
            user = self.get('user', key=key, _cached=True)
        elif username:
            user = self.get('user', username=username, _cached=True)
        else:
            user = self.get('user/current')
        return user

    def walk(self, path, **params):
        """ Walk a page tree recursively, and yield the root and all its children.
        """
        params = params.copy()
        depth_1st = params.pop('depth_1st', False)
        root_url = self.url(path)
        self.log.debug("Walking %r %s", root_url, 'depth 1st' if depth_1st else 'breadth 1st')

        stack = collections.deque([(0, [self.get(root_url, **params)])])
        while stack:
            depth, pages = stack.pop()
            for page in pages:
                ##import pprint; print('~ {:3d} {} '.format(depth, page.title).ljust(78, '~')); pprint.pprint(dict(page))
                yield depth, page
                children = self.getall(page._links.self + '/child/page', **params)
                if depth_1st:
                    for child in children:
                        stack.append((depth+1, [child]))
                else:
                    stack.appendleft((depth+1, children))
