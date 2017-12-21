#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'tong'


class Visitable(object):
    def __init__(self, dbtype, schema, tabledict=None, fielddict=None, root=None):
        self.dbtype = dbtype
        self.schema = schema
        self.tabledict = tabledict or {}
        self.fielddict = fielddict or {}
        self.root = root

    @classmethod
    def accept(cls, expr):
        return True

    @property
    def args(self):
        return self.dbtype, self.schema, self.tabledict, self.fielddict, self.root


class Visitor(Visitable):
    def visit(self, expr):
        for visitor in [Query, Value, Expression, Columns, Column, Table, CaseWhen]:
            if visitor.accept(expr):
                visitor(*self.args).visit(expr)


class Query(Visitor):
    def visit(self, expr):
        self.root = expr
        for key, exp in expr.items():
            if key == 'query':
                for k in exp:
                    self.access(k, exp[k])
            else:
                self.access(key, exp)

    def access(self, key, expr):
        if key == 'key':
            return
        expr['key'] = key
        for visitor in [Select, From, Where, Groupby, Orderby, Limit, OtherAttr]:
            if visitor.accept(expr):
                visitor(*self.args).visit(expr)
        expr.pop('key')

    @classmethod
    def accept(cls, expr):
        from query import util
        return util.contain(expr, ['selectList']) or util.contain(expr, ['query', 'fetch'])


class Column(Visitable):
    def __init__(self, *args):
        super(Column, self).__init__(*args)
        self._table = None
        self._name = None

    def table(self, expr):
        if self._table:
            return self._table
        names = expr.get('names')
        if len(names) == 1:
            self._table, self._name = None, names[0]
        else:
            self._table, self._name = names[0], names[1]
        return self._table

    def field(self, expr):
        if self._name:
            return self._name
        names = expr.get('names')
        if len(names) == 1:
            self._table, self._name = None, names[0]
        else:
            self._table, self._name = names[0], names[1]
        return self._name

    def visit(self, expr):
        names = []
        if self.table(expr) is not None:
            table = self.table(expr)
            names.append(self.tabledict.get(table.lower(), table))
        if self.field(expr) is not None:
            field = self.field(expr)
            names.append(self.fielddict.get(field.lower(), field))
        expr['names'] = names

    @classmethod
    def accept(cls, expr):
        from query import util
        return util.contain(expr, ['names']) and expr.get('key') != 'from'


class Table(Visitable):
    def __init__(self, *args):
        super(Table, self).__init__(*args)
        self._names = None

    def names(self, expr):
        if not self._names:
            self._names = expr.get('names') or []
        return [name for name in self._names]

    def visit(self, expr):
        names = self.names(expr)
        if self.schema:
            expr['schema'] = self.schema
        expr['names'] = [self.tabledict.get(name.lower(), name) for name in names]

    @classmethod
    def accept(cls, expr):
        from query import util
        return util.contain(expr, ['names']) and expr.get('key') == 'from'


class Expression(Visitable):
    def visit(self, expr):
        if expr['operator']['name'].lower() == 'as':
            Visitor(*self.args).visit(expr['operands'][0])
            return
        if expr['operator']['name'].lower() == 'over':
            expr['root'] = self.root
        expr['dbtype'] = self.dbtype
        for _ in expr['operands']:
            Visitor(*self.args).visit(_)

    @classmethod
    def accept(cls, expr):
        from query import util
        return util.contain(expr, ['operator', 'operands'])


class Columns(Visitable):
    def visit(self, expr):
        for column in (expr.get('list') or []):
            Visitor(*self.args).visit(column)

    @classmethod
    def accept(cls, expr):
        if 'list' not in expr:
            return False
        return all([(Expression.accept(_) or Column.accept(_)) for _ in expr['list']])


class Value(Visitable):
    def visit(self, expr):
        pass

    @classmethod
    def accept(cls, expr):
        from query import util
        return util.contain(expr, ['scale', 'isExact', 'value', 'typeName', 'prec']) or \
               (util.contain(expr, ['value', 'typeName']) and isinstance(expr['value'], dict)) or \
               (util.contain(expr, ['typeName']) and str(expr['typeName']).lower() == 'null')


class CaseWhen(Visitable):
    def whenList(self, expr):
        return [Visitor(*self.args).visit(item) for item in expr['whenList']['list']]

    def thenList(self, expr):
        return [Visitor(*self.args).visit(item) for item in expr['thenList']['list']]

    def elseExpr(self, expr):
        return Visitor(*self.args).visit(expr['elseExpr'])

    def visit(self, expr):
        self.whenList(expr)
        self.thenList(expr)
        self.elseExpr(expr)

    @classmethod
    def accept(cls, expr):
        from query import util
        return util.contain(expr, ['whenList', 'thenList', 'elseExpr'])


class Limit(Visitable):
    def visit(self, expr):
        expr['dbtype'] = self.dbtype

    @classmethod
    def accept(cls, expr):
        return expr.get('key') == 'fetch'


class Select(Columns):
    def visit(self, expr):
        super(Select, self).visit(expr)

    @classmethod
    def accept(cls, expr):
        return expr.get('key') == 'selectList'


class From(Visitable):
    def visit(self, expr):
        Visitor(*self.args).visit(expr)

    @classmethod
    def accept(cls, expr):
        return expr.get('key') == 'from'


class Where(Visitable):
    def visit(self, expr):
        Visitor(*self.args).visit(expr)

    @classmethod
    def accept(cls, expr):
        return expr.get('key') == 'where'


class Orderby(Visitable):
    def visit(self, expr):
        if expr.get('list'):
            Visitor(*self.args).visit(expr)

    @classmethod
    def accept(cls, expr):
        return expr.get('key') == 'orderList'


class Groupby(Visitable):
    def visit(self, expr):
        if expr.get('list'):
            Visitor(*self.args).visit(expr)

    @classmethod
    def accept(cls, expr):
        return expr.get('key') == 'groupBy'


class OtherAttr(Visitable):
    def visit(self, clause):
        pass

    @classmethod
    def accept(cls, expr):
        return expr.get('key') == 'keywordList'


if __name__ == '__main__':
    import sys
    import json
    sys.path.append('..')
    with open('../conf/test.json') as fp:
        text = fp.read()
    data = json.loads(text)
    Visitor(None, None, {"T2": "faker"}, {"A": "age", "B": "name"}).visit(data)
    print json.dumps(data)
