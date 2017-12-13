#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import time
from tornado import gen
from utils.handler import BaseHandler

__author__ = 'tong'


class OverviewHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        status = self.application.query_executor.status()
        result = []
        for item in status.values():
            result.append({
                'time': time.time() - item['time'],
                'connector': str(item['connector'])[7:-1],
                'sql': item['sql']
            })
        self.response(result=result)
