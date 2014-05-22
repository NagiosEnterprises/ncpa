#!/usr/bin/env python

import psapi
import win32pdh
import time
import os


class WindowsCountersNode(psapi.LazyNode):

    def parse_query(self, path, sleep=0):
        counter_path = os.path.join(*path)
        counter_path = '\\' + counter_path
        return self.get_counter_val(counter_path, sleep)

    def get_counter_val(self, counter_path, sleep=0, *args, **kwargs):
        query = win32pdh.OpenQuery()
        counter = win32pdh.AddCounter(query, counter_path)
        win32pdh.CollectQueryData(query)
        time.sleep(sleep)
        win32pdh.CollectQueryData(query)
        _, _, _, _, _, _, _, info, _ = win32pdh.GetCounterInfo(counter, False)
        units = info[-1]
        counter_type, value = win32pdh.GetFormattedCounterValue(counter, win32pdh.PDH_FMT_DOUBLE)
        win32pdh.CloseQuery(query)
        return {counter_path: [value, units]}


def get_counters_node():
    return WindowsCountersNode('windowscounters')

