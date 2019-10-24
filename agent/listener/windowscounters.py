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
                error = self.handle_error(exc, counter_path)
                return [ error, '' ]

        self.method = counter_method
        return super(WindowsCountersNode, self).walk(*args, **kwargs)

    def run_check(self, *args, **kwargs):
        path = self.path
        self.name = WindowsCountersNode.get_counter_path(path)

        try:
            def counter_method(*args, **kwargs):
                return WindowsCountersNode.get_counter_val(self.name, *args, **kwargs)

            self.method = counter_method
            return super(WindowsCountersNode, self).run_check(capitalize=False, *args, **kwargs)
        except Exception as exc:
            error = self.handle_error(exc, self.name)
            return { 'stdout': error, 'returncode': 3 }
            
    # For certain errors, we should add more info
    def handle_error(self, exc, name):
        error = exc.strerror

        if 'No data' in error:
            error = error + ' Does the counter (' + name  + ') exist?'
            logging.debug(exc)
        elif 'not valid' in error:
            error = error + ' You may need to add the sleep=1 parameter.'
            logging.debug(exc)
        elif 'negative value' in error:
            error = error + ' You may need to add the format=1 parameter.'
            logging.debug(exc)
        else:
            logging.exception(exc)

        return error

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

        # Allow using PDH_FMT_LONG for certain counter types if it is required
        fmt = win32pdh.PDH_FMT_DOUBLE
        try:
            fmt = int(kwargs['format'][0])
            if fmt == 1:
                fmt = win32pdh.PDH_FMT_LONG
        except (KeyError, TypeError, IndexError):
            pass

        query = win32pdh.OpenQuery()
        try:
            counter = win32pdh.AddEnglishCounter(query, counter_path)
            try:

                if factor != 0:
                    # Multiply results by 10^(factor) to get around limitations on threshold types
                    win32pdh.SetCounterScaleFactor(counter, factor)

                win32pdh.CollectQueryData(query)

                if sleep != 0:
                    time.sleep(sleep)
                    win32pdh.CollectQueryData(query)

                _, _, _, _, _, _, _, info, _ = win32pdh.GetCounterInfo(counter, False)
                _, value = win32pdh.GetFormattedCounterValue(counter, fmt)

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
        # ^                            -- Next character matched must be the beginning of the string
        #  ([^(/]*)                    -- match an arbitrary amount of non-left-paren, non-slash characters, capture
        #                                 (This capture group contains the object name)
        #           \(?                -- Optionally match (
        #              (.*?)           -- Optionally match anything and capture
        #                                 (This capture group contains the instance name)
        #                   \)?        -- Optionally match )
        #                      /       -- match a forward slash
        #                       (.*)   -- Match any characters after the slash and capture
        #                                 (This capture group contains the counter name)
        #                           $  -- Last character matched must be end of string
        # End result after split() is length-5 array. indices 1-3 refer to the capture groups
        wpc_regex = r'^([^(/]*)\(?(.*?)\)?/(.*)$'
        match_list = re.split(wpc_regex, wpc_string) 
        counter_path = '\\'
        if match_list[2]:
            counter_path += match_list[1] + '(' + match_list[2] + ')\\' + match_list[3]
        else:
            counter_path += match_list[1] + '\\' + match_list[3]
        return counter_path

def get_node():
    return WindowsCountersNode('windowscounters', None)