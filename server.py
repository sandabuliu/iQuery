#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import signal
import logging
import traceback
import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado.web import StaticFileHandler

from utils.config import config
from utils.handler import BaseHandler
from utils.futures import PoolExecutor, SQLTree

__author__ = 'tong'


root_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))


class Server(object):
    @property
    def logger(self):
        return logging.getLogger('runtime')

    def sig_handler(self, sig, frame):
        self.logger.info('Caught signal: %s\nTraceback (most recent call last):\n%s' %
                         (sig, ''.join(traceback.format_stack(frame))))
        tornado.ioloop.IOLoop.instance().add_callback(self.shutdown)

    def shutdown(self):
        deadline = time.time() + 40 * 60

        self.logger.info('Stopping http server')
        self.server.stop()
        self.logger.info('Will shutdown in %s seconds ...', (deadline-time.time()))
        io_loop = tornado.ioloop.IOLoop.instance()

        def stop():
            io_loop.stop()
            self.logger.info('Shutdown')

        def stop_loop():
            now = time.time()
            if now < deadline and io_loop._callbacks:
                self.logger.info('seconds: %s, callbacks: %s' %
                                 (deadline - now, io_loop._callbacks))
                io_loop.add_timeout(now + 1, stop_loop)
            else:
                stop()
        stop_loop()

    def __init__(self, app, port=8000):
        self.port = port
        self.server = tornado.httpserver.HTTPServer(app)
        self.debug = app.settings.get('debug', False)

    def setup_logger(self):
        if not self.debug:
            logging.getLogger().addHandler(logging.NullHandler())
        else:
            logger = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] [%(trace_id)s]: %(message)s')
            logger.setFormatter(formatter)
            logging.getLogger().addHandler(logger)

    def start(self, num_processes=1):
        signal.signal(signal.SIGTERM, self.sig_handler)
        signal.signal(signal.SIGINT, self.sig_handler)

        self.setup_logger()
        self.server.bind(self.port)
        self.server.start(num_processes)
        sys.stdout.write("listen server on port %s (pid: %s) ...\n" % (self.port, os.getpid()))
        tornado.ioloop.IOLoop.instance().start()


class Application(tornado.web.Application):
    def __init__(self, api, default_host="", transforms=None, **settings):
        source = os.path.join(root_path, 'resource', 'SQLParser.java')
        self.api = api
        self.handlers = []
        self.base_dir = os.path.dirname(os.path.join(root_path, api))
        self.load_handlers(api)
        self.executor = PoolExecutor(config['pool_size'])
        self.sql_tree = SQLTree(source, config['jre_exe'])
        super(Application, self).__init__(self.handlers, default_host, transforms, **settings)

    def load(self, filename):
        handler, ext = os.path.splitext(filename)
        route_path = handler[len(self.base_dir):]
        module_name = route_path.strip('/').replace('/', '.')
        __import__(module_name)
        module = sys.modules.get(module_name)
        for name in dir(module):
            if name.startswith('_'):
                continue
            obj = getattr(module, name)
            if not hasattr(obj, '__bases__'):
                continue
            if BaseHandler not in obj.__bases__:
                continue
            route = os.path.dirname(route_path)
            route = '%s/%s' % (route, obj.__name__.lower().split('handler')[0])
            self.handlers.append((route, obj))
            print 'routing uri %s -> %s' % (route, obj)

    def load_handlers(self, api):
        __import__(api)

        api_dir = os.path.join(root_path, api)
        for parent, dirnames, filenames in os.walk(api_dir):
            for name in filenames:
                if not name.endswith('.py'):
                    continue
                if name.startswith('_'):
                    continue

                self.load(os.path.join(parent, name))
        self.handlers.append((r'^/(.*?)$', StaticFileHandler, {"path": os.path.join(root_path, "static"),
                                                               "default_filename": "index.html"}))

    def log_request(self, handler):
        if hasattr(handler, 'log_request'):
            handler.log_request()
        else:
            super(Application, self).log_request(handler)
