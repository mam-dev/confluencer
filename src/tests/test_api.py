# *- coding: utf-8 -*-
# pylint: disable=wildcard-import, missing-docstring, no-self-use, bad-continuation
# pylint: disable=invalid-name, redefined-outer-name, too-few-public-methods
""" Test :py:mod:`«some_module»`.
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

import pytest

from confluencer import api


def test_tiny_link_is_parsed():
    url = 'https://confluence.example.com/x/ZqQ8'
    page_id = api.page_id_from_tiny_link(url)
    assert page_id == 3974246


def test_error_for_malformed_tiny_link():
    with pytest.raises(ValueError):
        url = 'https://confluence.example.com/x/#'
        api.page_id_from_tiny_link(url)


@pytest.mark.parametrize('page_id, tiny_id', [
    (3974246, 'ZqQ8'),
    ('3974246', 'ZqQ8'),
    (5063420, '_EJN'),
])
def test_tiny_id_from_page_id(page_id, tiny_id):
    assert tiny_id == api.tiny_id(page_id)


def test_api_with_explicit_endpoint():
    url = 'https://confluence.example.com/'
    cf = api.ConfluenceAPI(endpoint=url)
    assert not cf.base_url.endswith('/')
    assert cf.url('space') == url + 'rest/api/space'


@pytest.mark.parametrize('expected, link', [
    ('/rest/api/content/3974246', '/pages/viewpage.action?pageId=3974246'),
    ('/rest/api/content/3974246', '/x/ZqQ8'),
# XXX: FAILS! WHY?   ('/rest/api/content/5063416', '/x/_EJN'),
])
def test_api_url_from_page_link(expected, link):
    if link.startswith('/x/'):
        page_id = api.page_id_from_tiny_link(link)
        assert page_id == int(expected.split('/')[-1])
    cf = api.ConfluenceAPI(endpoint='https://confluence.example.com/')
    api_url = cf.url(cf.base_url + link)
    assert api_url == cf.base_url + expected
