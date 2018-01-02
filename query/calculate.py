#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
from util import random_field, random_table
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

    def attr(self, name, default=None):
        return self._column.get(name, default)

    @property
    def query(self):
        classes = self.__class__.__subclasses__()
        for cls in classes:
            if cls.__name__ == self.type:
                return cls(self.maker, self._query, self._column).query
            if cls.__subclasses__():
                classes += cls.__subclasses__()
        return self._query

    def over(self, aggr=None, partition_by=None, order_by=None):
        if not aggr:
            function = self._column
        else:
            function = Function.create(aggr, self._column)
        over = Over.create(function, partition_by=partition_by, order_by=order_by)
        table = self._query.froms[0]
        over['dbtype'] = self.maker.dbtype
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


class Annular(Calculate):
    @property
    def query(self):
        query = self.maker.query()
        join_on = []
        for x in self.xaxis:
            name = random_field()
            join_on.append(name)
            x = x.label(name)
            query.append_column(x)
            query = query.group_by(Column(x.name))
        name = random_field()
        column = Visitor(self._column).visit()
        query.append_column(column.label(name))

        field = random_field()
        query = query.alias(random_table())

        self._query.append_column(column.label(field))

        if self.attr('result_type') == 'rate':
            value = (Column(field) - query.columns[name])/query.columns[name]
        else:
            value = Column(field) - query.columns[name]
        self.maker.add_value(value)
        self.maker.add_join(query, [
            query.columns.get(name) == Column(self.maker.xalias[i])
            for i, name in enumerate(join_on)
        ])
        return self._query

    @property
    def xaxis(self):
        from visitor import Function
        result = []
        for x in self.maker.xaxis:
            v = Visitor(x).visit()
            if not Function.accept(x):
                result.append(v)
                continue
            result.append(self.next_time(x))
        return result

    def next_time(self, expr):
        from visitor import Function
        expr = copy.deepcopy(expr)
        operator = Function(expr).operator
        if operator.startswith('cast'):
            name = operator.replace('cast', 'next')
            operands = expr['operands']
            expr['operands'] = [Function.create(name, *operands)]
        expr = Function(expr)
        visitor = expr.visit()
        return visitor


class Same(Annular):
    def next_time(self, expr):
        from visitor import Function
        expr = copy.deepcopy(expr)
        operator = Function(expr).operator
        if operator.startswith('cast'):
            name = 'next_%s' % self.attr('unit', 'year')
            operands = expr['operands']
            expr['operands'] = [Function.create(name, *operands)]
        expr = Function(expr)
        visitor = expr.visit()
        return visitor
