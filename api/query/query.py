#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import json
from tornado import gen

from query.query import Query
from query.engine import Engine
from utils.visitor import Visitor
from query.connector import Connector
from utils.handler import BaseHandler
from utils.constants import DEFAULT_PORT

__author__ = 'tong'


class ResultHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        args = self.parse_args([
            {'name': 'type', 'required': True, 'location': 'args', 'cast': lambda x: x.lower()},
            {'name': 'host', 'required': True, 'location': 'args'},
            {'name': 'port', 'required': False, 'location': 'args', 'cast': int},
            {'name': 'username', 'required': False, 'location': 'args'},
            {'name': 'password', 'required': False, 'location': 'args'},
            {'name': 'alias', 'required': False, 'location': 'args'},
            {'name': 'schema', 'required': False, 'location': 'args'},
            {'name': 'sql', 'required': True, 'location': 'args'},
            {'name': 'kwargs', 'required': False, 'location': 'args', 'cast': json.loads}
        ])
        sql = args.pop('sql')
        args.setdefault('port', DEFAULT_PORT.get(self.args['type']))
        args.update(args.pop('kwargs', {}))
        connector = Connector(**args)

        tree = yield self.gen_tree(sql)
        Visitor(connector.type, connector.schema).visit(tree)
        query = Query.load(tree, connector)
        data = yield self.async_do(query.execute)
        self.response(data=data.data, columns=data.schema)


class SQLHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        args = self.parse_args([
            {'name': 'sql', 'required': True, 'location': 'args'},
            {'name': 'schema', 'required': False, 'location': 'args'},
            {'name': 'type', 'required': True, 'location': 'args'}
        ])
        tree = yield self.gen_tree(args['sql'])
        Visitor(args['type'], args.get('schema')).visit(tree)
        query = Query.load(tree, Engine.create(args['type']))
        self.response(sql=str(query))


class TreeHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        args = self.parse_args([
            {'name': 'sql', 'required': True, 'location': 'args'}
        ])
        tree = yield self.gen_tree(args['sql'])
        self.response(tree=tree)
