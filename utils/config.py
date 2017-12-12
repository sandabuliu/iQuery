#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from ConfigParser import ConfigParser

__author__ = 'tong'


class C(ConfigParser):
    ConfigParser._boolean_states[''] = False

    def get(self, section, option, raw=None, vars=None):
        try:
            return ConfigParser.get(self, section, option)
        except Exception:
            return raw


cfg = C()
cfg.read(os.getenv('IQUERY_CONF', 'conf/iquery.conf'))


config = dict(
    log_cfg=cfg.get('config', 'log_cfg'),
    log_dir=cfg.get('config', 'log_dir'),
    port=int(cfg.get('config', 'port', 8000)),
    pool_size=int(cfg.get('config', 'port', 50)),
    jre_exe=cfg.get('config', 'jre', 'java')
)
