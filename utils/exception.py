#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado.web import HTTPError

__author__ = 'tong'


class InternalError(HTTPError):
    def __init__(self, method, url, body, e):
        super(InternalError, self).__init__(500, 'METHOD: %s, URL: %s, BODY: %s, ERROR: %s' % (method, url, body, e))


class DriverError(Exception):
    pass
