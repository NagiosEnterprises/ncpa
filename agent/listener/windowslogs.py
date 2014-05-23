#!/usr/bin/env python

"""A plugin checking event logs on Windows is expected to take the following inputs:

Event Log Inclusion/Exclusion Fields
------------------------------------

Log Names - Expected to accept a list of strings that are names of logs that will be included
Event ID - Expected to accept a list of strings to be tested against Event ID fields of Event Logs
Category - Expected to accept a list of strings to be tested against Category fields of Event Logs
Severity - Expected to accept a list of strings to be tested against Severity fields of Event Logs
Message - Expected to accept of list of regular expressions to be tested against the Message fields of the logs
Application - Expected to accept a list of strings to be tested against the Application fields of Event Logs

Time Specific Fields
--------------------

Logged After - Should contain exactly one date for which the plugin will use for fetching logs. This date
               is to be considered a relative timedelta from which the log was written. For example, an
               input of 5d means the log was created in the past 5 days. Similarly, 13h would mean the
               log was created in the past 13 hours. Supported timeframe suffixes are:

* h - Hours
* m - minutes
* M - months
* w - weeks
* d - days

Nagios Specific Fields
----------------------

Type - Must be either *total* or *individual*. If type is total then the Nagios ranges will only take
       the total count of logs returned into account when calculating warning and critical. If
       type is individual, then the number of logs found in each log specified by Log Names will
       taken into account when calculating warning and critical values for the check.
Warning - Normal Nagios warning value, should accept the usual Nagios range values
Critical - Normal Nagios warning value, should accept the usual Nagios range values

Expected Standard Out
---------------------

Expected standard out for a plugin will list the filtered log count of each individual log specified
by Log Names. It should also contain the summed value of all log counts. Perfdata should contain
all log counts as well with corresponding Log Names for labels. Standard out should also contain a human readable
adaptation of the input Logged After specification.


"""

import psapi


class WindowsLogsNode(psapi.LazyNode):

    def run(self, path, *args, **kwargs):
        if args == []:
            return {self.name: []}
        else:
            return {self.name: kwargs}


def get_logs_node():
    return WindowsLogsNode('logs')
