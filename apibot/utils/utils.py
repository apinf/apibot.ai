# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import urllib.request


def url_is_alive(url):
    """
    Checks that a given URL is reachable.
    Source: https://gist.github.com/dehowell/884204
    :param url: A URL
    :rtype: bool
    """

    try:
        request = urllib.request.Request(url)
        request.get_method = lambda: 'HEAD'
        response = urllib.request.urlopen(request)
        return response.getcode() == 200
    except:
        return False
