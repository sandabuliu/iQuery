#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = 'tong'


class ResultProxy(object):
    def __init__(self, result):
        self._result = result
        self._data = None

    @property
    def data(self):
        if self._data is None:
            self._data = self._result.fetchall()
        return [list(_) for _ in self._data]

    @property
    def schema(self):
        return [{'name': key, 'type': self.ttype(key)} for key in self._result.keys()]

    @property
    def columns(self):
        return self._result.keys()

    @property
    def json_data(self):
        return [dict(zip(self.columns, _)) for _ in self.data]

    def ttype(self, name):
        try:
            return self._result._metadata._keymap[name][1][0].type.python_type
        except:
            return self._ttype(name)

    def _ttype(self, name):
        ttype = object
        try:
            for res in self._data:
                if res[name] is None:
                    continue
                ttype = type(res[name])
                break
        except:
            return ttype
        return ttype

    def __str__(self):
        from pandas import DataFrame
        return str(DataFrame(self.data, columns=[c['name'] for c in self.schema]))
