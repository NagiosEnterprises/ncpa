#!/usr/bin/env python

import nodes
import win32pdh
import time
import logging
import copy
import re
from urllib import unquote


class WindowsCountersNode(nodes.LazyNode):

    def accessor(self, path, config, full_path, args):
        new_node = copy.deepcopy(self)
        new_node.path = path
        new_node.config = config
        return new_node

    def walk(self, *args, **kwargs):

        if not getattr(self, 'path', None) or not self.path:
            return {self.name: []}

        path = self.path
        counter_path = WindowsCountersNode.get_counter_path(path)

        def counter_method(*args, **kwargs):
            try:
                return WindowsCountersNode.get_counter_val(counter_path, *args, **kwargs)
            except Exception as exc:
                return [['Error: %s' % exc.strerror], 'c']

        self.method = counter_method
        return super(WindowsCountersNode, self).walk(*args, **kwargs)

    def run_check(self, *args, **kwargs):
        path = self.path
        self.name = WindowsCountersNode.get_counter_path(path)

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

        try:
            factor = int(kwargs['factor'][0])
        except (KeyError, TypeError, IndexError):
            factor = 0

        query = win32pdh.OpenQuery()
        try:
            counter = win32pdh.AddCounter(query, counter_path)
            try:

                if factor != 0:
                    # Multiply results by 10^(factor) to get around limitations on threshold types
                    win32pdh.SetCounterScaleFactor(counter, factor)

                win32pdh.CollectQueryData(query)

                if sleep != 0:
                    time.sleep(sleep)
                    win32pdh.CollectQueryData(query)

                _, _, _, _, _, _, _, info, _ = win32pdh.GetCounterInfo(counter, False)
                _, value = win32pdh.GetFormattedCounterValue(counter, win32pdh.PDH_FMT_DOUBLE)
            finally:
                win32pdh.RemoveCounter(counter)
        finally:
            win32pdh.CloseQuery(query)

        unit = info[-1]

        if not isinstance(value, (int, long)):
            value = round(value, 2)

        return [value, unit]

    @staticmethod
    def get_counter_path(path):
        wpc_string = '/'.join(path)

        # Regex explanation
        # ^                                   -- Next character matched must be the beginning of the string
        #  ([^()/]*)                          -- match an arbitrary amount of non-paren, non-slash characters, capture
        #           \(?                       -- Optionally match (
        #              ([^()]*?)              -- Optionally match anything except a paren, capture
        #                       \)?           -- Optionally match )
        #                          /          -- match a forward slash
        #                           ([^()]*)  -- Match maximum number of non-paren characters, capture
        #                                   $ -- Last character matched must be end of string
        # End result after split() is length-5 array. indices 1-3 refer to the capture groups
        wpc_regex = r'^([^(/]*)\(?(.*?)\)?/([^)]*)$'
        match_list = re.split(wpc_regex, wpc_string) 
        counter_path = '\\'
        if match_list[2]:
            counter_path += match_list[1] + '(' + match_list[2] + ')\\' + match_list[3]
        else:
            counter_path += match_list[1] + '\\' + match_list[3]
        return counter_path

def get_node():
    return WindowsCountersNode('windowscounters', None)