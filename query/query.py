#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import copy
import logging
from visitor import Visitor
from engine import ResultProxy
from connector import Connector
from calculate import Calculate


__author__ = 'tong'

logger = logging.getLogger('query')

OPS = ['MAX', 'MIN', 'SUM', 'AVG', 'COUNT']


class Query(object):
    def __init__(self, query):
        self._query = query
        self._tables = {}
        self._bindobj = None

    @classmethod
    def load(cls, expr, bindobj=None):
        query = Query(Visitor(expr).visit())
        query.bind(bindobj)
        return query

    @property
    def connector(self):
        return self._bindobj

    def bind(self, bindobj):
        from sqlalchemy.engine import Engine
        if not bindobj:
            return
        if isinstance(bindobj, Connector):
            self._bindobj = bindobj
            self._query.bind = bindobj.engine.engine
        elif isinstance(bindobj, Engine):
            self._query.bind = bindobj
        else:
            raise Exception('can not bind type: `[%s]%s`' % (type(bindobj), bindobj))

    def execute(self):
        start = time.time()
        logger.info('connector: %s, query: %s' % (self._bindobj, self))
        result = ResultProxy(self._query.execute())
        logger.info('connector: %s, query: %s, cost: %s' % (self._bindobj, self, time.time() - start))
        return result

    def __str__(self):
        def stringify(o):
            try:
                return str(o)
            except UnicodeEncodeError:
                return unicode(o).encode('utf8')

        obj = self._query.compile()
        if obj.params:
            raise Exception('sql contain params, sql: %s, params: %s' %
                            (stringify(obj).replace('\n', ' '), obj.params))
        return stringify(obj).replace('\n', ' ')


class QueryMaker(object):
    def __init__(self, dbtype, table, xaxis, yaxis, where=None, order=None, limit=None):
        self.dbtype = dbtype
        self._xaxis = xaxis
        self._yaxis = yaxis
        self._table = table
        self._where = where
        self._order = order
        self._limit = limit
        self._xalias = []

    @property
    def xaxis(self):
        return copy.deepcopy([Column.create(_)
                              if isinstance(_, basestring)
                              else _ for _ in self._xaxis])

    @property
    def xalias(self):
        return self._xalias

    def query(self):
        from sqlalchemy import Table, MetaData, select
        if isinstance(self._table, basestring):
            table = Table(self._table, MetaData())
        else:
            table = Table(self._table['name'], MetaData(schema=self._table['database']))
        return select().select_from(table)

    def value(self, query):
        for i, col in enumerate(self._yaxis):
            operator = str(col.get('operator', {}).get('name')).upper()
            if operator not in OPS:
                raise Exception('aggr function(%s) must be in %s' % (operator, OPS))
            if col.get('calculate'):
                query = Calculate(self, query, col).query
            else:
                col = self.column(col, 'y_%s' % i)
                query.append_column(col)
        return query

    def group(self, query):
        from sqlalchemy import Column
        if not self._xaxis:
            return query
        for i, col in enumerate(self._xaxis):
            col = self.column(col, 'x_%s' % i)
            self._xalias.append(col.name)
            query.append_column(col)
            query = query.group_by(Column(col.name))
        return query

    def where(self, query):
        from sqlalchemy import text
        if not self._where:
            return query
        if isinstance(self._where, basestring):
            return query.where(text(self._where))
        return Visitor(self._where).visit()

    def order(self, query):
        order = self._order or []
        for i, col in enumerate(order):
            query = query.order_by(self.column(col, 'o_%s' % i))
        return query

    def limit(self, query):
        from visitor import Limit
        if self._limit:
            return Limit(Limit.create(self._limit)).visit(query)
        return query

    def column(self, value, default_alias=None):
        from sqlalchemy import Column
        from sqlalchemy.sql.elements import Label
        if isinstance(value, basestring):
            col = Column(value)
            if default_alias:
                col = col.label(default_alias)
            return col
        col = Visitor(value).visit()
        if isinstance(col, Label):
            return col
        if default_alias:
            col = col.label(default_alias)
        return col

    def build(self):
        query = self.query()
        query = self.where(query)
        query = self.group(query)
        query = self.value(query)
        query = self.order(query)
        query = self.limit(query)
        return Query(query)


if __name__ == '__main__':
    import json
    logger.addHandler(logging.StreamHandler())
    # with open('../conf/test.json') as fp:
    #     text = fp.read()
    # data = json.loads(text)
    # q = Query.load(data, Connector(
    #     type='mysql', username='root', password='123456', host='192.168.1.150', port=3306, database='bin_test'
    # ))
    # print q
    # print query.execute()
    from visitor import Column, Function, TypeName, Desc

    x = Function.create('cast_year', Column.create('ctimestamp'))
    y = Function.create('count', Column.create('age'))
    y['calculate'] = 'accumulate'
    q = QueryMaker('mysql',
                   {'name': 'faker91', 'database': 'bin_test'},
                   [x], [y]).build()
    connector = Connector(
        type='mysql', username='root', password='123456', host='192.168.1.150', port=3306, database='bin_test'
    )
    print str(q)
    q.bind(connector)
    data = q.execute()
    print data.schema
    print data.data
