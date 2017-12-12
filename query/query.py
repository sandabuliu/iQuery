#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
from visitor import Visitor
from engine import ResultProxy
from connector import Connector


__author__ = 'tong'

logger = logging.getLogger('query')


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
        logger.info('connector: %s, query: %s' % (self._bindobj.connect_str, self))
        result = ResultProxy(self._query.execute())
        logger.info('connector: %s, query: %s, cost: %s' % (self._bindobj.connect_str, self, time.time() - start))
        return result

    def __str__(self):
        obj = self._query.compile()
        if obj.params:
            return ('%s ( %s )' % (obj, obj.params)).replace('\n', ' ')
        else:
            return str(obj).replace('\n', ' ')


if __name__ == '__main__':
    import json
    logger.addHandler(logging.StreamHandler())
    with open('../conf/test.json') as fp:
        text = fp.read()
    data = json.loads(text)
    query = Query.load(data, Connector(
        type='mysql', username='root', password='123456', host='192.168.1.150', port=3306, database='bin_test'
    ))
    print query
    # print query.execute()
