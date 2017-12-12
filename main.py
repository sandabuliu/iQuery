#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging.config
from server import Application, Server
from tornado.options import define, options, parse_command_line

from utils.config import config

__author__ = 'tong'

define("port", help="service listening port")
define("debug", help="debug mode", default=False)
define("processors", help="the number of process", default=1)


if __name__ == '__main__':
    parse_command_line()
    if not os.path.exists(config['log_dir']):
        os.makedirs(config['log_dir'])
    logging.config.fileConfig(config['log_cfg'], defaults={'log_dir': config['log_dir']})

    port = int(options.port or config['port'])
    application = Application('api', debug=options.debug)
    application.listening_port = port

    server = Server(application, port)
    server.start(options.processors)
