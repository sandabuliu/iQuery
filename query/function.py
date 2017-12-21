#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = 'tong'


def get_type(name):
    from visitor import TypeName
    return TypeName(TypeName.create(name)).visit()


class Function(object):
    def __init__(self, dbtype):
        self.dbtype = dbtype

    def visit(self, func_name):
        from sqlalchemy.sql import func, case
        func_entry = {
            'entry': {
                'cast': lambda x, y: func.cast(x, y),
                'cast_day': lambda x: func.cast(x, get_type('date')),
                'cast_month': lambda x: self.visit('concat')(
                    self.visit('year')(x), self.visit_param('-'), self.visit('month')(x)
                ),
                'cast_quarter': lambda x: self.visit('concat')(
                    self.visit('year')(x), self.visit('quarter')(x), self.visit_param('Q')
                ),
                'cast_year': lambda x: self.visit('year')(x)
            },
            'oracle': {
                'if': lambda x, y, z: case([(x, y)], else_=z),
                'concat': lambda *args: reduce(func.concat, args),
                'year': lambda x: func.to_char(x, self.visit_param('yyyy')),
                'month': lambda x: func.to_char(x, self.visit_param('mm')),
                'day': lambda x: func.to_char(x, self.visit_param('dd'))
            },
            'postgresql': {
                'if': lambda x, y, z: case([(x, y)], else_=z),
                'year': lambda x: func.to_char(x, self.visit_param('yyyy')),
                'month': lambda x: func.to_char(x, self.visit_param('mm')),
                'day': lambda x: func.to_char(x, self.visit_param('dd'))
            },
            'db2': {
                'concat': lambda *args: reduce(func.concat, args),
                'if': lambda x, y, z: case([(x, y)], else_=z)
            },
            'hana': {
                'if': lambda x, y, z: case([(x, y)], else_=z),
                'concat': lambda *args: reduce(func.concat, args),
                'year': lambda x: func.to_char(x, self.visit_param('yyyy')),
                'month': lambda x: func.to_char(x, self.visit_param('mm')),
                'day': lambda x: func.to_char(x, self.visit_param('dd'))
            },
            'mssql': {
                'if': lambda x, y, z: case([(x, y)], else_=z),
                'concat': lambda *args: reduce(lambda a, b: a+b, map(
                    lambda x: func.cast(x, get_type('string')), args
                ))
            }
        }
        et = func_entry.get('entry')
        et.update(func_entry.get(self.dbtype, {}))
        return self.wrap(et.get(func_name) or getattr(func, func_name))

    def visit_param(self, value):
        from sqlalchemy import text
        if isinstance(value, basestring):
            return text("'%s'" % value)
        if isinstance(value, (int, float, long)):
            return text('%s' % value)
        return value

    def wrap(self, func):
        def _func(*args):
            return func(*[self.visit_param(_) for _ in args])
        return _func
