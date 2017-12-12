#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import util
import copy
import logging
from constants import types, quote

__author__ = 'tong'

logger = logging.getLogger('query')


class Visitable(object):
    def __init__(self, expr=None):
        expr = expr or {}
        if not self.accept(expr):
            raise Exception('Visitor `%s` can not visit %s: %s' % (self.__class__.__name__, expr.keys(), expr))
        self._expr = expr

    @classmethod
    def accept(cls, expr):
        return True

    @property
    def dbtype(self):
        return self._expr.get('dbtype')


class Visitor(Visitable):
    def __init__(self, expr):
        super(Visitor, self).__init__(expr)
        self._expr = copy.deepcopy(expr)
        if 'query' in self._expr:
            query = self._expr.pop('query')
            self._expr.update(query)

    def visit(self):
        for visitor in [Query, Value, Expression, ValueList, Column, Table, TypeName, CaseWhen]:
            if visitor.accept(self._expr):
                clause = visitor(self._expr).visit()
                return clause
        logger.warn('Expr (%s) can not parse, return None' % json.dumps(self._expr))
        return None


class Query(Visitor):
    def visit(self):
        self._expr['selectList']['key'] = 'selectList'
        clause = Select(self._expr['selectList']).visit()
        self._expr['selectList'].pop('key')

        for key, expr in self._expr.items():
            if key == 'key':
                continue
            if key == 'selectList':
                continue
            expr['key'] = key
            clause = self.access(clause, expr)
            expr.pop('key')
        return clause

    def access(self, clause, expr):
        for visitor in [From, Where, Groupby, Orderby, Limit, OtherAttr]:
            if visitor.accept(expr):
                return visitor(expr).visit(clause)
        return clause

    @classmethod
    def accept(cls, expr):
        return util.contain(expr, ['selectList'])


class Column(Visitable):
    @property
    def table(self):
        names = self._expr.get('names')
        if len(names) == 1:
            return None
        return names[0]

    @property
    def name(self):
        names = self._expr.get('names')
        if not names:
            return None
        if len(names) == 1:
            return names[0]
        return names[1]

    def visit(self, clause=None):
        from sqlalchemy import Table, Column, MetaData
        if clause:
            return clause.columns[self.name]
        if self.name:
            column = Column(self.name)
        else:
            column = '*'
        if self.table:
            column.table = Table(self.table, MetaData())
        return column

    @classmethod
    def accept(cls, expr):
        return util.contain(expr, ['names']) and expr.get('key') != 'from'


class Table(Visitable):
    @property
    def name(self):
        return self._expr.get('names', [None])[-1]

    @property
    def schema(self):
        if len(self._expr.get('names', [])) > 1:
            return self._expr['names'][0]
        return self._expr.get('schema')

    def visit(self):
        from sqlalchemy import Table, MetaData
        return [Table(self.name, MetaData(schema=self.schema))]

    @classmethod
    def accept(cls, expr):
        return util.contain(expr, ['names']) and expr.get('key') == 'from'


class TypeName(Visitable):
    @property
    def typename(self):
        return self._expr['typeName']['names'][0]

    def visit(self):
        return types[self.typename.lower()]

    @classmethod
    def accept(cls, expr):
        return util.contain(expr, ['typeName']) and isinstance(expr['typeName'], dict)

    @classmethod
    def create(cls, typename):
        return TypeName({'typeName': {'names': [typename]}})


class Expression(Visitable):
    @property
    def operator(self):
        return self._expr['operator']['name'].lower()

    @property
    def operands(self):
        return [Visitor(_).visit() for _ in self._expr['operands']]

    def visit(self):
        for visitor in self.__class__.__subclasses__():
            if visitor.accept(self._expr):
                return visitor(self._expr).visit()
        return self.operate()[self.operator](*self.operands)

    @classmethod
    def operate(cls):
        from sqlalchemy.sql.elements import and_, or_
        return {
            'and': lambda a, b: and_(a, b),
            'or': lambda a, b: or_(a, b),
            '=': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
            '<>': lambda a, b: a != b,
            '>=': lambda a, b: a >= b,
            '<=': lambda a, b: a <= b,
            '>': lambda a, b: a > b,
            '<': lambda a, b: a < b,
            '+': lambda a, b: a + b,
            '-': lambda a, b: a - b,
            '*': lambda a, b: a - b,
            '/': lambda a, b: a / b,
            'like': lambda a, b: a.like(b),
            'not like': lambda a, b: a.notlike(b),
            'is null': lambda a: a == None,
            'is not null': lambda a: a != None,
            'between': lambda a, b, c: a.between(b, c)
        }

    @classmethod
    def accept(cls, expr):
        return util.contain(expr, ['operator', 'operands'])


class Function(Expression):
    @property
    def distinct(self):
        if not self._expr.get('functionQuantifier'):
            return False
        try:
            value = self._expr['functionQuantifier']['value']
            if isinstance(value, basestring):
                return value.lower() == 'distinct'
            return value['name']['value'].lower() == 'distinct'
        except:
            return False

    @property
    def operands(self):
        operands = super(Function, self).operands
        if self.distinct:
            if len(operands) == 1:
                operands[0] = operands[0].distinct()
            else:
                # 多参数 distinct 的情况目前没有
                raise Exception("unsupported operating: multi-params's distinct")
        return operands

    def visit(self):
        from function import Function
        entry = Function(self.dbtype).visit(self.operator)
        return entry(*self.operands)

    @classmethod
    def accept(cls, expr):
        if not Expression.accept(expr):
            return False
        operator = Expression(expr).operator
        if operator in cls.operate():
            return False
        if any([_.accept(expr) for _ in Expression.__subclasses__() if _ != cls]):
            return False
        return True


class In(Expression):
    def visit(self):
        from sqlalchemy import text
        op1, op2 = self.operands
        return text('%s %s (%s)' % (
            self.visit_element(op1), self.operator.upper(),
            ','.join([self.visit_element(_) for _ in op2])
        ))

    def visit_element(self, value):
        from sqlalchemy import dialects, Column
        from sqlalchemy.sql.elements import TextClause
        if isinstance(value, TextClause):
            return value.text
        if isinstance(value, Column) and self.dbtype:
            dialect = dialects.registry.load(self.dbtype)
            preparer = dialect.preparer(dialect())
            return preparer.format_column(value)
        return str(value)

    @classmethod
    def accept(cls, expr):
        if not Expression.accept(expr):
            return False
        return Expression(expr).operator.lower() == 'in' or \
            Expression(expr).operator.lower() == 'not in'


class As(Expression):
    @property
    def operands(self):
        op = self._expr['operands']
        return [Visitor(op[0]).visit(), op[1]['names'][0]]

    def visit(self):
        from sqlalchemy.sql import Select
        op1, op2 = self.operands
        if isinstance(op1, Select):
            return op1.alias(op2)
        else:
            return op1.label(op2)

    @classmethod
    def accept(cls, expr):
        if not Expression.accept(expr):
            return False
        return Expression(expr).operator.lower() == 'as'


class Desc(Expression):
    def visit(self):
        column = Column(self._expr['operands'][0]).visit()
        return column.desc()

    @classmethod
    def accept(cls, expr):
        if not Expression.accept(expr):
            return False
        return Expression(expr).operator.lower() == 'desc'


class ValueList(Visitable):
    @property
    def list(self):
        if isinstance(self._expr, list):
            return self._expr
        return self._expr.get('list') or []

    def visit(self):
        ret = []
        for column in self.list:
            ret.append(Visitor(column).visit())
        return ret or ['*']

    @classmethod
    def accept(cls, expr):
        if isinstance(expr, list):
            expr = {'list': expr}
        if 'list' not in expr:
            return False
        return all([(
             Expression.accept(_) or
             Column.accept(_) or
             Value.accept(_)
         ) for _ in expr['list']])


class Value(Visitable):
    @property
    def value(self):
        if util.contain(self._expr, ['scale', 'isExact', 'value', 'typeName', 'prec']):
            return self._expr.get('value')
        return self._expr['value']['value']

    @property
    def type(self):
        return self._expr['typeName']

    def visit(self):
        if self.type.lower() == 'null':
            return None
        return quote[self.type.lower()](self.value)

    @classmethod
    def accept(cls, expr):
        return util.contain(expr, ['scale', 'isExact', 'value', 'typeName', 'prec']) or \
               (util.contain(expr, ['value', 'typeName']) and isinstance(expr['value'], dict)) or \
               (util.contain(expr, ['typeName']) and str(expr['typeName']).lower() == 'null')


class CaseWhen(Visitable):
    @property
    def whenList(self):
        return [Visitor(item).visit() for item in self._expr['whenList']['list']]

    @property
    def thenList(self):
        return [Visitor(item).visit() for item in self._expr['thenList']['list']]

    @property
    def elseExpr(self):
        return Visitor(self._expr['elseExpr']).visit()

    def visit(self):
        from sqlalchemy import case
        then = self.thenList
        return case([(when, then[i]) for i, when in enumerate(self.whenList)], else_=self.elseExpr)

    @classmethod
    def accept(cls, expr):
        return util.contain(expr, ['whenList', 'thenList', 'elseExpr'])


class Limit(Visitable):
    def visit(self, clause):
        value = Visitor(self._expr).visit()
        if value is not None:
            return self.limit(clause, value)
        return clause

    def limit(self, clause, value):
        from sqlalchemy import text
        if self.dbtype in ('db2', 'mssql'):
            if not isinstance(value, type(text(''))):
                return clause.limit(value)
            return clause.limit(int(value.text))
        return clause.limit(value)

    @classmethod
    def accept(cls, expr):
        return expr.get('key') == 'fetch'


class Select(ValueList):
    def visit(self):
        from sqlalchemy import select
        columns = super(Select, self).visit()
        return select(columns)

    @classmethod
    def accept(cls, expr):
        return expr.get('key') == 'selectList'


class From(Visitable):
    @property
    def tables(self):
        tables = Visitor(self._expr).visit()
        if not isinstance(tables, list):
            tables = [tables]
        return tables

    def visit(self, clause):
        for table in self.tables:
            clause = clause.select_from(table)
        return clause

    @classmethod
    def accept(cls, expr):
        return expr.get('key') == 'from'


class Where(Visitable):
    @property
    def whereclause(self):
        if self._expr:
            return Visitor(self._expr).visit()
        return None

    def visit(self, clause):
        whereclause = self.whereclause
        if whereclause is not None:
            return clause.where(whereclause)
        return clause

    @classmethod
    def accept(cls, expr):
        return expr.get('key') == 'where'


class Orderby(Visitable):
    @property
    def columns(self):
        if self._expr.get('list'):
            return Visitor(self._expr).visit()
        return None

    def visit(self, clause):
        columns = self.columns
        if columns:
            return clause.order_by(*columns)
        return clause

    @classmethod
    def accept(cls, expr):
        return expr.get('key') == 'orderList'


class Groupby(Visitable):
    @property
    def columns(self):
        if self._expr.get('list'):
            return Visitor(self._expr).visit()
        return None

    def visit(self, clause):
        columns = self.columns
        if columns:
            return clause.group_by(*columns)
        return clause

    @classmethod
    def accept(cls, expr):
        return expr.get('key') == 'groupBy'


class OtherAttr(Visitable):
    @property
    def list(self):
        return self._expr.get('list') or []

    def visit(self, clause):
        for attr in self.list:
            if attr['value'].lower() == 'distinct':
                clause = clause.distinct()
        return clause

    @classmethod
    def accept(cls, expr):
        return expr.get('key') == 'keywordList'


if __name__ == '__main__':
    with open('../conf/oracle.json') as fp:
        text = fp.read()
    data = json.loads(text)
    print Visitor(data).visit()
