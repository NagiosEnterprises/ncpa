#!/usr/bin/env python

import nodes
import win32pdh
import time
import os
import logging
import copy


class WindowsCountersNode(nodes.LazyNode):

    def accessor(self, path, config, full_path):
        new_node = copy.deepcopy(self)
        new_node.path = path
        new_node.config = config
        return new_node

    def walk(self, *args, **kwargs):

        if not getattr(self, 'path', None) or not self.path:
            return { self.name: [] }

        path = self.path
        counter_path = os.path.join('\\', *path)

        def counter_method(*args, **kwargs):
            try:
                return WindowsCountersNode.get_counter_val(counter_path, *args, **kwargs)
            except Exception as exc:
                return [['Error: %s' % exc.strerror], 'c']

        self.method = counter_method
        return super(WindowsCountersNode, self).walk(*args, **kwargs)

    def run_check(self, *args, **kwargs):
        path = self.path
        self.name = os.path.join('\\', *path)

        def counter_method(*args, **kwargs):
            try:
                return WindowsCountersNode.get_counter_val(self.name, *args, **kwargs)
            except Exception as exc:
                logging.exception(exc)
                return [0, 'c']

        self.method = counter_method
        return super(WindowsCountersNode, self).run_check(capitalize=False, *args, **kwargs)

    @staticmethod
    def get_counter_val(counter_path, *args, **kwargs):
        try:
            sleep = float(kwargs['sleep'][0])
        except (KeyError, TypeError, IndexError):
            sleep = 0

        query = win32pdh.OpenQuery()
        counter = win32pdh.AddCounter(query, counter_path)
        win32pdh.CollectQueryData(query)
        time.sleep(sleep)
        win32pdh.CollectQueryData(query)
        _, _, _, _, _, _, _, info, _ = win32pdh.GetCounterInfo(counter, False)
        _, value = win32pdh.GetFormattedCounterValue(counter, win32pdh.PDH_FMT_DOUBLE)
        win32pdh.CloseQuery(query)

        unit = info[-1]

        if not isinstance(value, (list, tuple)):
            value = [value]

        return [value, unit]

def get_node():
    return WindowsCountersNode('windowscounters', None)