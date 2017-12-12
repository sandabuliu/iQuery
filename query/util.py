#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = 'tong'


def contain(data, keys):
    return set(data).issuperset(set(keys))


def storage_id(tree):
    if 'query' in tree:
        return storage_id(tree['query'])
    if 'from' in tree:
        return storage_id(tree['from'])
    if 'operands' in tree:
        return storage_id(tree['operands'][0])
    if 'names' in tree:
        return tree['names'][0].lower()
