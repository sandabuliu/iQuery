#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import json
from toolz import merge
from tornado import gen

from query.query import QueryMaker
from query.connector import Connector
from query.visitor import Column, Function

from utils.handler import BaseHandler
from utils.constants import DEFAULT_PORT

__author__ = 'tong'


class ResultHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        self.parse_args([
            {'name': 'type', 'required': True, 'location': 'args', 'cast': lambda x: x.lower()},
            {'name': 'host', 'required': True, 'location': 'args'},
            {'name': 'port', 'required': False, 'location': 'args', 'cast': int},
            {'name': 'username', 'required': False, 'location': 'args'},
            {'name': 'password', 'required': False, 'location': 'args'},
            {'name': 'alias', 'required': False, 'location': 'args'},
            {'name': 'database', 'required': False, 'location': 'args'},
            {'name': 'kwargs', 'required': False, 'location': 'args', 'cast': json.loads},

            {'name': 'table', 'required': True, 'location': 'body'},
            {'name': 'where', 'required': False, 'location': 'body'},
            {'name': 'order', 'required': False, 'location': 'body'},
            {'name': 'xAxis', 'required': False, 'location': 'body', 'default': []},
            {'name': 'yAxis', 'required': True, 'location': 'body'},
            {'name': 'limit', 'required': False, 'location': 'body'},
        ])
        connector = Connector(**self.connect_info)

        query = QueryMaker(self.type, self.table, self.xAxis, self.yAxis,
                           where=None, order=self.order, limit=self.limit).build()
        query.bind(connector)
        data = yield self.async_do(query.execute)
        self.response(data=data.data, columns=data.schema)

    @property
    def connect_info(self):
        params = {'type': self.type, 'port': self.port}
        for key, value in self.args.items():
            if key in ['host', 'username', 'password', 'alias']:
                params[key] = value
        return merge(params, self.args.get('kwargs', {}))

    @property
    def where(self):
        return self.args.get('where')

    @property
    def order(self):
        order = self.args.get('order')
        if not order:
            return None
        if not isinstance(order, list):
            return [order]
        return order

    @property
    def limit(self):
        return self.args.get('limit')

    @property
    def table(self):
        table = self.args['table']
        if not isinstance(self.args['table'], dict):
            table = {"name": table}

        if 'database' in table:
            return table
        table['database'] = self.args.get('database')
        return table

    @property
    def port(self):
        return self.args.get('port') or DEFAULT_PORT.get(self.type)

    @property
    def type(self):
        return str(self.args['type']).lower()

    @property
    def xAxis(self):
        axis = self.args['xAxis']
        if not isinstance(axis, list):
            axis = [axis]

        result = []
        for x in axis:
            if isinstance(x, dict):
                result.append(Function.create(x['func'], *[Column.create(_) for _ in x['params']]))
            else:
                result.append(Column.create(x))
        return result

    @property
    def yAxis(self):
        axis = self.args['yAxis']
        if not isinstance(axis, list):
            axis = [axis]

        result = []
        for y in axis:
            if isinstance(y, dict):
                aggr = y.get('func') or 'COUNT'
                func = Function.create(aggr, Column.create(y['name']))
                if y.get('calculate'):
                    func['calculate'] = y['calculate']
                result.append(func)
            else:
                result.append(Function.create('COUNT', Column.create(y)))
        return result
