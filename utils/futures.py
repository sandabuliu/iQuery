#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time
import subprocess
from tornado import gen
from tornado.process import Subprocess
from concurrent.futures import ThreadPoolExecutor


__author__ = 'tong'


class QueryExecutor(ThreadPoolExecutor):
    def __init__(self, max_works):
        super(QueryExecutor, self).__init__(max_works)
        self.futures = {}

    def submit(self, fn, *args, **kwargs):
        future = super(QueryExecutor, self).submit(fn, *args, **kwargs)
        query = fn.im_self
        self.futures[id(future)] = {'time': time.time(), 'sql': str(query),
                                    'connector': query.connector, 'future': future}
        future.add_done_callback(self.finish)
        return future

    def finish(self, future):
        self.futures.pop(id(future))

    def status(self):
        return self.futures


class SQLTree(object):
    def __init__(self, source, jre_exe='java'):
        resource = os.path.abspath(os.path.dirname(source))
        lib_path = os.path.join(resource, 'lib')

        jar = resource
        if os.path.exists(lib_path):
            filenames = [os.path.join(lib_path, _) for _ in
                         os.listdir(lib_path) if _.endswith('.jar')]
            jar += ':'+':'.join([_ for _ in filenames if os.path.isfile(_)])

        self.params = '-classpath %s' % jar
        self.jre_exe = jre_exe

        if os.path.exists(os.path.join(resource, 'SQLParser')):
            return
        cmd = "%sc %s %s" % (self.jre_exe, self.params, source)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.wait() != 0:
            err = p.stderr.read()
            raise Exception('javac build failed (%s), error: %s' % (cmd, err))

    @gen.coroutine
    def gen_tree(self, sql):
        command = "%s %s SQLParser '%s'" % (self.jre_exe, self.params, sql)
        process = Subprocess(
            command, shell=True,
            stdout=Subprocess.STREAM,
            stderr=Subprocess.STREAM,
        )
        out, err = yield [process.stdout.read_until_close(), process.stderr.read_until_close()]
        try:
            result = json.loads(out)
        except:
            raise Exception('java run failed (%s), error: %s' % (command.encode('utf8'), err))
        raise gen.Return(result)
