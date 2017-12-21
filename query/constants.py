#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import text
from sqlalchemy.sql import sqltypes

__author__ = 'tong'


types = {
    'double': sqltypes.Numeric,
    'string': sqltypes.String,
    'int': sqltypes.INT,
    'integer': sqltypes.Integer,
    'char': sqltypes.CHAR,
    'date': sqltypes.DATE
}


quote = {
    'decimal': lambda x: text('%s' % x),
    'string': lambda x: text("'%s'" % x),
    'char': lambda x: text("'%s'" % x),
}
