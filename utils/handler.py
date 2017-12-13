#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import uuid
import logging
from random import randint
from functools import wraps

from tornado import gen
from tornado.concurrent import Future
from tornado.web import RequestHandler, HTTPError, MissingArgumentError

__author__ = 'tong'


class LogTracer(logging.Filter):
    def __init__(self, name=''):
        super(LogTracer, self).__init__(name)
        self.trace_id = None

    def filter(self, record):
        record.trace_id = self.trace_id
        return True


class BaseHandler(RequestHandler):
    api_logger = logging.getLogger('api')
    logger = logging.getLogger('runtime')
    log_tracer = LogTracer()
    logger.addFilter(log_tracer)
    api_logger.addFilter(log_tracer)
    logging.getLogger('query').addFilter(log_tracer)

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.request_start_time = 0
        self.process_start_time = 0
        self.process_end_time = 0
        self.status_code = 200
        self.result = {'message': ''}
        self.trace_id = None
        self.user_id = None
        self.args = None
        self.async_do = self.application.query_executor.submit
        self.gen_tree = self.application.sql_tree.gen_tree
        for method in self.SUPPORTED_METHODS:
            method = method.lower()
            method_func = getattr(self, method)
            if method_func:
                setattr(self, method, self.handler_wrap(method_func))

    def handler_wrap(self, func):
        @gen.coroutine
        @wraps(func)
        def _func(*args, **kwargs):
            self.process_start_time = time.time()
            try:
                ret = func(*args, **kwargs)
                if isinstance(ret, Future):
                    yield ret
            except HTTPError, e:
                self.response(e.status_code, str(e))
                self.logger.error(e, exc_info=True)
            except Exception, e:
                self.response(500, "Interal error: %s" % e)
                self.logger.error(e, exc_info=True)
            finally:
                self.process_end_time = time.time()
            self.do_response()
        return _func

    def do_response(self):
        try:
            self.set_header("Content-Type", "application/json;charset=utf-8")
            self.add_header("Connection", "keep-alive")
            self.set_status(self.status_code)
            self.write(json.dumps(self.result, cls=JSONEncoder))
            self.finish('\n')
        except Exception, e:
            self.logger.error('response format error: %s, data: %s' % (str(e), self.result), exc_info=True)
            self.status_code = 500
            self.set_status(500, 'response format error: %s' % str(e))
            self.write(json.dumps({'status': '500', 'message': 'response format error: %s' % str(e)}))
            self.finish('\n')

    def prepare(self):
        self.request_start_time = time.time()
        self.process_start_time = self.request_start_time
        self.process_end_time = self.request_start_time
        self.status_code = 200
        self.trace_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, '%s%s' % (time.time(), randint(0, 100000))))
        self.request.query_arguments.pop('trace_id', None)
        self.result = {'message': ''}
        self.log_tracer.trace_id = self.trace_id

    def response(self, status_code=200, message='', **kwargs):
        self.status_code = status_code
        if message:
            kwargs['message'] = message.strip()
        self.result = kwargs

    def location(self, name):
        if name == 'args':
            return {key: self.get_argument(key) for key in self.request.query_arguments}
        elif name == 'body':
            return json.loads(self.request.body or '{}')
        elif name == 'form':
            return {key: self.get_body_argument(key) for key in self.request.body_arguments}

    def parse_args(self, arg_list):
        results = {}
        for arg in arg_list:
            location = arg.get('location')
            required = arg.get('required')

            name = arg.get('name')
            cast = arg.get('cast')
            para = self.location(location)
            if name not in para:
                if 'default' in arg:
                    para[name] = arg['default']
                elif required:
                    raise MissingArgumentError(name)
                else:
                    continue
            value = para.get(name)
            if cast:
                try:
                    value = cast(value)
                except Exception, e:
                    raise HTTPError(400, "Invalid %s(%s): %s" % (str(cast), name, e))

            results[name] = value
        self.args = results
        return results

    def log_request(self):
        request_end_time = time.time()
        pending = int((self.process_start_time - self.request_start_time) * 1000)
        process = int((self.process_end_time - self.process_start_time) * 1000)
        tornado = int((request_end_time - self.process_end_time) * 1000)
        ip = self.request.headers.get('X-Real-Ip') or self.request.remote_ip
        uri = self.request.path
        args = self.request.query_arguments
        params = '&'.join(["%s=%s" % (key, self.get_query_argument(key)) for key in args]).replace('\n', ' ')
        log = u'[{ip}] [{meth} {uri}] [{params}] [{body}] [{status_code}] {pending} {process} {tornado} {all}'.format(
            ip=ip, uri=uri, params=params,
            status_code=self.status_code, body=self.request.body,
            pending=pending, process=process,
            tornado=tornado, meth=self.request.method,
            all=int((request_end_time - self.request_start_time) * 1000)
        )

        if self.status_code != 200:
            self.api_logger.error(log)
        else:
            self.api_logger.info(log)

    def data_received(self, chunk):
        pass


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        import pandas
        from decimal import Decimal
        from datetime import datetime, date, time, timedelta

        if obj == type(None):
            return None
        if isinstance(obj, type):
            return obj.__name__
        if isinstance(obj, type(pandas.NaT)):
            return None
        if isinstance(obj, timedelta):
            return obj.total_seconds()
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(obj, date):
            return obj.strftime('%Y-%m-%d 00:00:00')
        if isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        if isinstance(obj, Decimal):
            return str(obj)
        return super(JSONEncoder, self).default(obj)