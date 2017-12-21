#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = 'tong'


def contain(data, keys):
    return set(data).issuperset(set(keys))
