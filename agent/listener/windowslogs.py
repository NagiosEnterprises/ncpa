# !/usr/bin/env python

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
import nodes
import datetime
import win32evtlog
import re
import win32evtlogutil
import win32con
import pywintypes
import database
import time
import server
import ConfigParser


class WindowsLogsNode(nodes.LazyNode):

    def walk(self, *args, **kwargs):
        logtypes = get_logtypes(kwargs)
        filters = get_filter_dict(kwargs)

        def log_method(*args, **kwargs):
            return WindowsLogsNode.get_logs(logtypes, filters, *args, **kwargs)

        self.method = log_method
        return { self.name: self.method(*args, **kwargs) }

    @staticmethod
    def get_logs(logtypes, filters, *args, **kwargs):
        logs = {}
        server = kwargs.get('server', None)
        if server:
            server = server[0]

        for logtype in logtypes:
            try:
                logs[logtype] = get_event_logs(server, logtype, filters)
            except pywintypes.error as exc:
                raise Exception('Windows error occurred while getting log %s: %r' % (logtype, exc.strerror))
            except BaseException as exc:
                logging.exception(exc)
                raise Exception('General error occurred while getting log %s: %r' % (logtype, exc))

        # If the logs are empty, and we had no name selected, give a good
        # explanation of what is going on instead of being empty
        if not logtypes and not logs:
            return { 'message': 'No log type selected. Select log types using \'name=<type>\'. Example: api/logs?name=System. Multiple log types can be selected.' }

        return logs, 'logs'

    def run_check(self, *args, **kwargs):
        try:
            logs = self.walk(*args, **kwargs)['logs'][0]
            log_names = sorted(logs.keys())
        except Exception as exc:
            return { 'stdout': 'UNKNOWN: %s, cannot continue meaningfully.' % exc.message,
                     'returncode': 3 }

        log_counts = [len(logs[x]) for x in log_names]

        self.set_warning(kwargs)
        self.set_critical(kwargs)
        self.set_log_check(kwargs)
        self.get_delta_values(log_counts, kwargs, *args, **kwargs)

        returncode = 0
        prefix = 'OK'

        if self.is_warning(log_counts, log_names):
            returncode = 1
            prefix = 'WARNING'
        if self.is_critical(log_counts, log_names):
            returncode = 2
            prefix = 'CRITICAL'

        log_names.append('Total Count')
        log_counts.append(sum(log_counts))
        logged_after = kwargs.get('logged_after', None)
        if not logged_after is None:
            logged_after = logged_after[0]
        nice_timedelta = self.translate_timedelta(logged_after)

        perfdata = ' '.join(["'%s'=%d;%s;%s;" % (name, count, ''.join(self.warning), ''.join(self.critical)) for name, count in
                             zip(log_names, log_counts)])
        info = ', '.join(['%s has %d logs' % (name, count) for name, count in zip(log_names, log_counts)])
        info_line = '%s: %s (Time range - %s)' % (prefix, info, nice_timedelta)

        stdout = '%s | %s' % (info_line, perfdata)

        # Long output including actual log messages
        for n in log_names:
            if n == 'Total Count':
                continue
            stdout += '\n%s Logs\nTime: Computer: Severity: Event ID: Source: Message\n-----------------------------------\n' % n
            for log in logs[n]:
                stdout += '%s: %s: %s: %s: %s: %s\n' % (log['time_generated'], log['computer_name'], log['severity'],
                    log['event_id'], log['application'], log['message'].replace('\r\n', ''))

        # Get the check logging value
        try:
            check_logging = int(kwargs['config'].get('general', 'check_logging'))
        except Exception as e:
            check_logging = 1

        # Put check results in the check database
        if not server.__INTERNAL__ and check_logging == 1:
            db = database.DB()
            current_time = time.time()
            db.add_check(kwargs['accessor'].rstrip('/'), current_time, current_time, returncode,
                         stdout, kwargs['remote_addr'], 'Active')

        return { 'stdout': stdout, 'returncode': returncode }

    @staticmethod
    def translate_timedelta(time_delta):
        if not time_delta:
            return 'last 24 hours'
        num, suffix = time_delta[:-1], time_delta[-1]
        if suffix == 's':
            nice_name = 'second'
        elif suffix == 'm':
            nice_name = 'minute'
        elif suffix == 'h':
            nice_name = 'hour'
        elif suffix == 'd':
            nice_name = 'day'
        elif suffix == 'w':
            nice_name = 'week'
        elif suffix == 'M':
            nice_name = 'month'
        if int(num) > 1:
            nice_name += 's'
        return 'last %s %s' % (num, nice_name)

    def set_log_check(self, request_args):
        log_check = request_args.get('type', 'all')
        if log_check != 'all':
            self.log_check = 'individual'
        else:
            self.log_check = 'all'

    def is_warning(self, log_counts, log_names):
        if not self.warning:
            return False

        warnings = []

        if self.log_check == 'all':
            return self.is_within_range(self.warning, sum(log_counts))
        else:
            for count in log_counts:
                if self.is_within_range(self.warning, count):
                    warnings.append(True)
                else:
                    warnings.append(False)
            return any(warnings)

    def is_critical(self, log_counts, log_names):
        if not self.critical:
            return False

        criticals = []

        if self.log_check == 'all':
            return self.is_within_range(self.critical, sum(log_counts))
        else:
            for count in log_counts:
                if self.is_within_range(self.critical, count):
                    criticals.append(True)
                else:
                    criticals.append(False)
            return any(criticals)


def get_logtypes(request_args):
    logtypes = request_args.get('name', [])
    #if logtypes is None:
    #    logtypes = ['Application', 'Security', 'Setup', 'System', 'Forwarded Events']
    return logtypes


def get_filter_dict(request_args):
    fdict = {}
    for key in request_args:
        value = request_args[key]
        if key == 'event_id':
            fdict['EventID'] = value
        elif key == 'application':
            fdict['SourceName'] = value
        elif key == 'computer_name':
            fdict['ComputerName'] = value
        elif key == 'category':
            fdict['EventCategory'] = value
        elif key == 'message':
            fdict['Message'] = value
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


def get_node():
    return WindowsLogsNode('logs', None)


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
    elif time_frame == 'h':
        return datetime.timedelta(hours=offset)
    elif time_frame == 'd':
        return datetime.timedelta(days=offset)
    elif time_frame == 'w':
        return datetime.timedelta(weeks=offset)
    elif time_frame == 'M':
        offset = 4 * offset
        return datetime.timedelta(weeks=offset)
    else:
        raise TypeError('Unknown time_frame, Given: %r, expected /smdhwM/', time_frame)


def get_datetime_from_date_input(date_input):
    try:
        offset, time_frame = date_input[:-1], date_input[-1]
        offset = abs(int(offset))
        t_delta = get_timedelta(offset, time_frame)
    except (IndexError, TypeError) as exc:
        logging.error('Date input was invalid, Given: %r, %r', date_input, exc)
        t_delta = datetime.timedelta(days=1)
    return t_delta


def datetime_from_event_date(evt_date):
    """
    This function converts dates with format '12/23/99 15:54:09' to seconds since 1970.

    Note - NS:
    The fact that this is required is really dubious. Not sure why the win32 API
    doesn't take care of this, but alas, here we are.
    """
    date_string = str(evt_date)
    time_generated = datetime.datetime.strptime(date_string, '%m/%d/%y %H:%M:%S')
    return time_generated


def is_interesting_event(event, name, filters):
    for log_property in filters:
        if log_property == 'logged_after':
            continue
        restrictions = filters[log_property]
        for restriction in restrictions:
            value = getattr(event, log_property, None)

            # Special for Event ID
            if log_property == "EventID":
                value = str(value & 0x1FFFFFFF)
                if str(restriction) != value:
                    return False

            # Look in message
            if value is None and log_property == 'Message':
                safe = win32evtlogutil.SafeFormatMessage(event, name)
                if not re.search(restriction, safe):
                    return False

            # Do normal ==
            if not value is None:
                if str(restriction) != str(value):
                    return False
    return True


def normalize_event(event, name):
    safe_log = {}
    safe_log['message'] = win32evtlogutil.SafeFormatMessage(event, name)
    safe_log['event_id'] = str(event.EventID & 0x1FFFFFFF)
    safe_log['computer_name'] = str(event.ComputerName)
    safe_log['category'] = str(event.EventCategory)
    safe_log['severity'] = EVENT_TYPE.get(event.EventType, 'UNKNOWN')
    safe_log['application'] = str(event.SourceName)
    safe_log['time_generated'] = str(event.TimeGenerated)
    return safe_log


def get_event_logs(server, name, filters):
    handle = win32evtlog.OpenEventLog(server, name)
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    logs = []

    try:
        logged_after = filters['logged_after']
        logged_after = datetime.datetime.now() - logged_after
    except KeyError:
        logged_after = datetime.datetime.now() - datetime.timedelta(days=1)

    try:
        while True:
            events = win32evtlog.ReadEventLog(handle, flags, 0)
            if events:
                for event in events:
                    time_generated = datetime_from_event_date(event.TimeGenerated)
                    if time_generated < logged_after:
                        raise StopIteration
                    elif is_interesting_event(event, name, filters):
                        safe_log = normalize_event(event, name)
                        logs.append(safe_log)
            else:
                raise StopIteration
    except StopIteration:
        pass
    finally:
        win32evtlog.CloseEventLog(handle)
    return logs


def tail_method(last_ts, server=None, *args, **kwargs):
    filters = get_filter_dict(kwargs)
    filters['logged_after'] = datetime.timedelta(seconds=10)
    log_names = kwargs.get('name', None)

    if log_names is None:
        name = 'System'
    else:
        name = log_names[0]

    logs = get_event_logs(server, name, filters)
    newest_ts = last_ts
    non_dup_logs = []

    for log in logs:
        date_ts = datetime_from_event_date(log['time_generated'])
        if date_ts > newest_ts:
            newest_ts = date_ts
        if date_ts > last_ts:
            non_dup_logs.append(log)

    return newest_ts, non_dup_logs
