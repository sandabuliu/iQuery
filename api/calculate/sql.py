#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

from toolz import merge
from tornado import gen

from query.query import QueryMaker
from query.visitor import Column, Function

from utils.handler import BaseHandler
from utils.constants import DEFAULT_PORT

__author__ = 'tong'


class SQLHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        self.parse_args([
            {'name': 'type', 'required': True, 'location': 'args', 'cast': lambda x: x.lower()},
            {'name': 'table', 'required': True, 'location': 'body'},
            {'name': 'where', 'required': False, 'location': 'body'},
            {'name': 'order', 'required': False, 'location': 'body'},
            {'name': 'xAxis', 'required': False, 'location': 'body', 'default': []},
            {'name': 'yAxis', 'required': True, 'location': 'body'},
            {'name': 'limit', 'required': False, 'location': 'body'},
        ])
        query = QueryMaker(self.type, self.table, self.xAxis, self.yAxis,
                           where=self.where, order=self.order, limit=self.limit).build()
        self.response(result=str(query))

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
        else:
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
