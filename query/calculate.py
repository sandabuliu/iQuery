#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import func, text, case, select, Column
from visitor import Over, Function, Expression, Table, Visitor

__author__ = 'tong'


class Calculate(object):
    def __init__(self, maker, query, column):
        self.maker = maker
        self.dbtype = maker.dbtype
        self._query = query
        self._column = column

    @property
    def type(self):
        return self._column['calculate'].capitalize()

    @property
    def query(self):
        for cls in self.__class__.__subclasses__():
            if cls.__name__ == self.type:
                return cls(self.maker, self._query, self._column).query
        return self._query

    def over(self, aggr=None, partition_by=None, order_by=None):
        if not aggr:
            function = self._column
        else:
            function = Function.create(aggr, self._column)
        over = Over.create(function, partition_by=partition_by, order_by=order_by)
        table = self._query.froms[0]
        over['dbtype'] = 'mysql'
        over['root'] = {
            'from': Table.create(table.schema, table.name),
            'groupBy': {'list': self.maker.xaxis}
        }
        return over


class Percent(Calculate):
    @property
    def query(self):
        expr = Expression.create('/', self._column, self.over('SUM'))
        self._query.append_column(Expression(expr).visit())
        return self._query


class Repeat(Calculate):
    @property
    def query(self):
        columns = Visitor({'list': self._column['operands']}).visit()
        for col in columns:
            self._query = self._query.group_by(col)
        count = func.count(text('1'))
        self._query.append_column(count.label('count_num'))
        self._query.append_column(case([(count > text('1'), count)], else_=text('0')).label('repeat_num'))
        query = select().select_from(self._query.alias('repeat_table'))
        for name in self.maker.xalias:
            query = query.group_by(Column(name))
            query.append_column(Column(name))
        query.append_column(func.sum(Column('repeat_num'))/func.sum(Column('count_num')))
        return query


class Accumulate(Calculate):
    @property
    def query(self):
        expr = self.over('SUM', order_by=self.maker.xaxis)
        self._query.append_column(Over(expr).visit())
        return self._query
