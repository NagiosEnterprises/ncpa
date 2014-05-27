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
import logging
import psapi
import datetime
import win32evtlog
import re
import time
import win32evtlogutil
import win32con


class WindowsLogsNode(psapi.LazyNode):

    def run(self, path, *args, **kwargs):
        if args == []:
            return {self.name: []}
        else:
            self.request_args = kwargs
            logtypes = self.get_logtypes()
            filters = self.get_filter_dict()
            logs = {}
            for logtype in logtypes:
                try:
                    logs[logtype] = get_event_logs('localhost', logtype, filters)
                except BaseException as exc:
                    logging.exception(exc)
                    logs[logtype] = [{'error': 'Unable to access log: %r' % exc}]
            return {self.name: logs}

    def get_logtypes(self):
        logtypes = self.request_args.get('name', [])
        return logtypes

    def get_filter_dict(self):
        fdict = {}
        for key in self.request_args:
            value = self.request_args[key]
            if key == 'event_id':
                fdict['EventID'] = value
            elif key == 'application':
                fdict['SourceName'] = value
            elif key == 'computer_name':
                fdict['ComputerName'] = value
            elif key == 'category':
                fdict['EventCategory'] = value
            elif key == 'severity':
                fdict['EventType'] = [EVENT_TYPE.get(x, 'UNKNOWN') for x in value]
            elif key == 'logged_after':
                if isinstance(value, (str, unicode)):
                    logged_after = value
                else:
                    logged_after = value[0]
                logged_after = get_datetime_from_date_input(logged_after)
                fdict['logged_after'] = logged_after
        return fdict


def get_logs_node():
    return WindowsLogsNode('logs')

EVENT_TYPE = {win32con.EVENTLOG_AUDIT_FAILURE: 'AUDIT_FAILURE',
              win32con.EVENTLOG_AUDIT_SUCCESS: 'AUDIT_SUCCESS',
              win32con.EVENTLOG_INFORMATION_TYPE: 'INFORMATION',
              win32con.EVENTLOG_WARNING_TYPE: 'WARNING',
              win32con.EVENTLOG_ERROR_TYPE: 'ERROR',
              'ERROR': win32con.EVENTLOG_ERROR_TYPE,
              'WARNING': win32con.EVENTLOG_WARNING_TYPE,
              'INFORMATION': win32con.EVENTLOG_INFORMATION_TYPE,
              'AUDIT_FAILURE': win32con.EVENTLOG_AUDIT_FAILURE,
              'AUDIT_SUCCESS': win32con.EVENTLOG_AUDIT_SUCCESS}


def get_timedelta(offset, time_frame):
    if time_frame == 's':
        return datetime.timedelta(seconds=offset)
    elif time_frame == 'm':
        return datetime.timedelta(minutes=offset)
    elif time_frame == 'd':
        return datetime.timedelta(days=offset)
    elif time_frame == 'w':
        return datetime.timedelta(weeks=offset)
    elif time_frame == 'M':
        offset = 4 * offset
        return datetime.timedelta(weeks=offset)
    else:
        raise TypeError('Unknown time_frame, Given: %r, expected /smdwM/', time_frame)


def get_datetime_from_date_input(date_input):
    try:
        offset, time_frame = date_input[:-1], date_input[-1]
        offset = abs(int(offset))
        t_delta = get_timedelta(offset, time_frame)
    except (IndexError, TypeError):
        logging.error('Date input was invalid, Given: %r', date_input)
        t_delta = datetime.timedelta(days=1)
    return t_delta


def date2sec(evt_date):
    """
    This function converts dates with format
    '12/23/99 15:54:09' to seconds since 1970.

    Note from NS:

    This was taken from:
    http://docs.activestate.com/activepython/2.4/pywin32/Windows_NT_Eventlog.html

    The fact that this is required is really dubious. I'm not sure why this was implemented
    in this in the win32 module.
    """
    regexp = re.compile('(.*)\\s(.*)')
    reg_result = regexp.search(evt_date)
    date = reg_result.group(1)
    the_time = reg_result.group(2)
    mon, day, year = [int(x) for x in date.split('/')]
    hour, minute, sec = [int(x) for x in the_time.split(':')]
    tup = [year, mon, day, hour, minute, sec, 0, 0, 0]

    sec = time.mktime(tup)

    return sec


def is_interesting_event(event, filters):
    for log_property in filters:
        if log_property == 'logged_after':
            continue
        restrictions = filters[log_property]
        for restriction in restrictions:
            value = getattr(event, log_property, None)
            if not value is None and str(value) != str(restriction):
                return False
    return True


def normalize_event(event, logtype):
    safe_log = {}
    safe_log['message'] = win32evtlogutil.SafeFormatMessage(event, logtype)
    safe_log['event_id'] = str(event.EventID)
    safe_log['computer_name'] = str(event.ComputerName)
    safe_log['category'] = str(event.EventCategory)
    safe_log['severity'] = EVENT_TYPE.get(event.EventType, 'UNKNOWN')
    safe_log['application'] = str(event.SourceName)
    safe_log['time_generated'] = str(event.TimeGenerated)
    return safe_log


def get_event_logs(server, logtype, filters):
    handle = win32evtlog.OpenEventLog(server, logtype)
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    logs = []

    try:
        logged_after = filters['logged_after']
        logged_after = datetime.datetime.now() - logged_after
    except KeyError:
        logged_after = datetime.datetime.now() - datetime.timedelta(days=1)
    logged_after = time.mktime(logged_after.timetuple())

    try:
        while True:
            events = win32evtlog.ReadEventLog(handle, flags, 0)
            if events:
                for event in events:
                    time_generated = date2sec(str(event.TimeGenerated))
                    if time_generated < logged_after:
                        raise StopIteration
                    if is_interesting_event(event, filters):
                        safe_log = normalize_event(event, logtype)
                        logs.append(safe_log)
    except StopIteration:
        pass
    finally:
        win32evtlog.CloseEventLog(handle)
    return logs

