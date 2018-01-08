#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from MySQLdb.cursors import Cursor
    Cursor._defer_warnings = True
except ImportError:
    Cursor = None


__author__ = 'tong'


class Connector(object):
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._engine = None
        self._tables = {}
        self.cstr = self._kwargs.pop('connect_str', None)
        self.type = self._kwargs.pop('type').lower()
        self.username = self._kwargs.pop('username', None)
        self.password = self._kwargs.pop('password', None)
        self.host = self._kwargs.pop('host', None)
        self.port = self._kwargs.pop('port', None)
        self.alias = self._kwargs.pop('alias', '') or ''
        self.schema = self._kwargs.pop('schema', None)
        self.connect_type = self._kwargs.pop('connect_type', None)

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def params(self):
        if not self._kwargs:
            return ''
        return '?%s' % '&'.join([('%s=%s' % (k, v)) for k, v in self._kwargs.items()])

    @property
    def tables(self):
        return self._tables

    @property
    def engine(self):
        from engine import Engine
        if not self._engine:
            self._engine = Engine(self)
        return self._engine

    @property
    def connect_str(self):
        if self.cstr:
            return self.cstr
        if self.password is None:
            user = self.username
        else:
            user = '%s:%s' % (self.username, self.password)
        return '%s%s://%s@%s:%s/%s%s' % (self.type, self.driver, user, self.host, self.port, self.alias, self.params)

    @property
    def driver(self):
        return {
            'mssql': '+pymssql'
        }.get(self.type, '')

    def connection(self):
        return self.engine.engine.connect()

    def reflect(self, only=None):
        only = only or []
        for name in only:
            self._tables[name] = self.engine.table(name)

    def __str__(self):
        if self._engine:
            return str(self.engine.engine)
        return self.connect_str
