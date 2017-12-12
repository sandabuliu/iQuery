#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from sqlalchemy.sql import select, visitors
from sqlalchemy import create_engine, MetaData
from connector import Connector
from proxy import ResultProxy

__author__ = 'tong'

logger = logging.getLogger('query')


class Engine(object):
    def __init__(self, connobj):
        self._connobj = connobj
        self._connect_str = self.get_connect_str(connobj)
        self._engine = self.create_engine()
        self._metadata = self.create_meta()
        self._table_names = None
        self._view_names = None

    @classmethod
    def create(cls, name):
        import MySQLdb
        MySQLdb.Cursor = None
        MySQLdb.version = '1.0.0'
        return create_engine('%s://' % name, module=MySQLdb)

    def create_engine(self):
        return create_engine(self._connect_str)

    def create_meta(self):
        return MetaData(self._engine)

    def get_connect_str(self, connobj):
        if isinstance(connobj, dict):
            self._connobj = Connector(**connobj)
            self._connobj._engine = self
            return self._connobj.connect_str
        elif isinstance(connobj, Connector):
            self._connobj._engine = self
            return connobj.connect_str
        elif isinstance(connobj, basestring):
            self._connobj = Connector(connect_str=connobj)
            self._connobj._engine = self
            return connobj
        raise Exception('Error %s\'connector type: %s(%s)' % (self.__class__.__name__, connobj, type(connobj)))

    def table(self, name):
        if name in self._metadata.tables:
            return self._metadata.tables[name]
        if name in self.tables():
            self._metadata.reflect(only=[name], views=True, schema=self._connobj.database)
            return self._metadata.tables[name]

    def databases(self):
        conn = self._engine.connect()
        dbs = self._engine.dialect.get_schema_names(conn)
        conn.close()
        return dbs

    def tables(self):
        conn = self._engine.connect()
        if not self._table_names:
            self._table_names = self._engine.dialect.get_table_names(conn, self._connobj.database)
        if not self._view_names:
            self._view_names = self._engine.dialect.get_view_names(conn, self._connobj.database)
        return [{'name': _, 'type': 'table'} for _ in self._table_names] + \
               [{'name': _, 'type': 'view'} for _ in self._view_names]

    def schema(self, table):
        if table not in self._metadata.tables:
            self._metadata.reflect(only=[table], schema=self._connobj.database)
        columns = self._engine.dialect.get_columns(self._engine, table, self._connobj.database)
        for column in columns:
            if isinstance(column['type'], visitors.VisitableType):
                column['type'] = column['type']().python_type
            else:
                column['type'] = column['type'].python_type
        return columns

    def preview(self, table, rows=100):
        if table not in self._metadata.tables:
            self._metadata.reflect(only=[table], schema=self._connobj.database)
        table = self._metadata.tables['%s.%s' % (self._connobj.database, table)]
        return ResultProxy(select([table]).limit(rows).execute())

    @property
    def engine(self):
        return self._engine


if __name__ == '__main__':
    c = Connector(type='mysql', username='root', password='123456',
                  host='192.168.1.150', port='3306', database='bin_test')
    engine = c.engine
    print engine.databases()
    print engine.tables()
    print engine.schema('faker')
    print engine.preview('faker', 10)
    print type(engine.preview('faker', 10))
