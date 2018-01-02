#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = 'tong'


def hash_str(obj):
    return 'n%s' % abs(hash(str(obj)))


def contain(data, keys):
    return set(data).issuperset(set(keys))


def random_table():
    import uuid
    return 'tb_%s' % str(uuid.uuid4())[:6]


def random_field():
    import uuid
    return 'fd_%s' % str(uuid.uuid4())[:6]


class DEFOver(object):
    def __init__(self, expr):
        self.expr = expr

    @property
    def table(self):
        import copy
        from visitor import Visitor
        root = self.expr.get('root', {})
        table = copy.deepcopy(root.get('from'))
        if table:
            table['key'] = 'from'
        return Visitor(table).visit()[0]

    @property
    def function(self):
        from visitor import Visitor
        return Visitor(self.expr['operands'][0]).visit()

    @property
    def is_native(self):
        from sqlalchemy.sql.functions import Function
        func = self.function
        params = self.params(func)
        if len(params) < 1:
            return True
        if isinstance(params[0], Function):
            return False
        return True

    @property
    def group(self):
        from visitor import ValueList
        root = self.expr.get('root', {})
        group = root.get('groupBy')
        if not group:
            return []
        return ValueList(group).visit()

    @property
    def partition_by(self):
        from visitor import ValueList
        if len(self.expr['operands']) < 2:
            return []
        args = self.expr['operands'][1]
        if args.get('partitionList'):
            return ValueList(args['partitionList']).visit()
        return []

    @property
    def order_by(self):
        from visitor import ValueList
        if len(self.expr['operands']) < 2:
            return []
        args = self.expr['operands'][1]
        if args.get('orderList'):
            return ValueList(args['orderList']).visit()
        return []

    @property
    def where(self):
        from visitor import Expression
        if not self.expr.get('root', {}).get('where'):
            return None
        where = self.expr['root'].get('where')
        return Expression(where).visit()

    def visit(self):
        if self.is_native:
            table, query = self.native()
        else:
            table, query = self.complex()

        for item in self.partition_by:
            query = query.where(self.column(item, table) == self.column(item))
        for item in self.order_by:
            query = query.where(self.column(item, table) <= self.column(item))
        return query.label(random_field())

    def column(self, column, table=None):
        from copy import deepcopy
        from sqlalchemy import text, Column
        from sqlalchemy.sql.functions import Function

        if hasattr(column, 'copy'):
            column = column.copy()
        else:
            column = deepcopy(column)
        is_null = table is None
        if isinstance(column, Column) and is_null:
            column.table = self.table
            return text(str(column))
        if isinstance(column, Function) and is_null:
            params = self.params(column)
            for param in params:
                self.column(param)
            return column
        if isinstance(column, Column) and not is_null:
            column.table = table
        if isinstance(column, Function) and not is_null:
            column = Column(hash_str(column))
            column.table = table
        return column

    def complex(self):
        from sqlalchemy import select, Column
        from sqlalchemy.sql.functions import Function
        where = self.where
        params = self.params()
        params = [_.label(random_field()) for _ in params]
        query = select(params).select_from(self.table)
        if where is not None:
            query = query.where(where)
        for col in self.group:
            if isinstance(col, Function):
                col = col.label(hash_str(col))
            query.append_column(col)
            query = query.group_by(col)
        query = query.alias(random_table())

        func = self.function
        func.clauses.clauses = [Column(_.name) for _ in params]
        return query, select([func]).select_from(query)

    def native(self):
        from sqlalchemy import select
        func = self.function
        if self.group:
            params = self.params(func)
            params[0] = params[0].distinct()
        table = self.table.alias(random_table())
        query = select([func]).select_from(table)
        where = self.where
        if where is not None:
            query = query.where(where)
        return table, query

    def params(self, function=None):
        function = self.function if function is None else function
        return function.clauses.clauses
