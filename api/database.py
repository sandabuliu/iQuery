#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import json
from tornado import gen

from query.connector import Connector
from utils.handler import BaseHandler
from utils.constants import DEFAULT_PORT

__author__ = 'tong'


class SchemasHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        args = self.parse_args([
            {'name': 'type', 'required': True, 'location': 'args', 'cast': lambda x: x.lower()},
            {'name': 'host', 'required': True, 'location': 'args'},
            {'name': 'port', 'required': False, 'location': 'args', 'cast': int},
            {'name': 'username', 'required': False, 'location': 'args'},
            {'name': 'password', 'required': False, 'location': 'args'},
            {'name': 'alias', 'required': False, 'location': 'args'},
            {'name': 'kwargs', 'required': False, 'location': 'args', 'cast': json.loads}
        ])
        args.setdefault('port', DEFAULT_PORT.get(self.args['type']))
        args.update(args.pop('kwargs', {}))
        connector = Connector(**args)
        schemas = yield self.async_do(connector.engine.schemas)
        self.response(schemas=schemas)


class TablesHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        args = self.parse_args([
            {'name': 'type', 'required': True, 'location': 'args', 'cast': lambda x: x.lower()},
            {'name': 'host', 'required': True, 'location': 'args'},
            {'name': 'port', 'required': False, 'location': 'args', 'cast': int},
            {'name': 'username', 'required': False, 'location': 'args'},
            {'name': 'password', 'required': False, 'location': 'args'},
            {'name': 'alias', 'required': False, 'location': 'args'},
            {'name': 'schema', 'required': True, 'location': 'args'},
            {'name': 'kwargs', 'required': False, 'location': 'args', 'cast': json.loads}
        ])
        args.setdefault('port', DEFAULT_PORT.get(self.args['type']))
        args.update(args.pop('kwargs', {}))
        connector = Connector(**args)
        tables = yield self.async_do(connector.engine.tables)
        self.response(tables=tables)


class ColumnsHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        args = self.parse_args([
            {'name': 'type', 'required': True, 'location': 'args', 'cast': lambda x: x.lower()},
            {'name': 'host', 'required': True, 'location': 'args'},
            {'name': 'port', 'required': False, 'location': 'args', 'cast': int},
            {'name': 'username', 'required': False, 'location': 'args'},
            {'name': 'password', 'required': False, 'location': 'args'},
            {'name': 'alias', 'required': False, 'location': 'args'},
            {'name': 'schema', 'required': True, 'location': 'args'},
            {'name': 'table', 'required': True, 'location': 'args'},
            {'name': 'kwargs', 'required': False, 'location': 'args', 'cast': json.loads}
        ])
        table = args.pop('table')
        args.setdefault('port', DEFAULT_PORT.get(self.args['type']))
        args.update(args.pop('kwargs', {}))
        connector = Connector(**args)
        columns = yield self.async_do(connector.engine.columns, table)
        self.response(columns=columns)
