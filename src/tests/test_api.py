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


def test_tiny_id_from_page_id():
    for i in (3974246, '3974246'):
        assert 'ZqQ8' == api.tiny_id(i)


def test_api_with_explicit_endpoint():
    url = 'https://confluence.example.com/'
    cf = api.ConfluenceAPI(endpoint=url)
    assert not cf.base_url.endswith('/')
    assert cf.url('space') == url + 'rest/api/space'


def test_api_url_from_page_link():
    cf = api.ConfluenceAPI(endpoint='https://confluence.example.com/')
    data = ('/x/ZqQ8', '/pages/viewpage.action?pageId=3974246')
    for url in data:
        assert cf.url(cf.base_url + url).endswith('/rest/api/content/3974246')
