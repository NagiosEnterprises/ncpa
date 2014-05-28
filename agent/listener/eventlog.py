import windowslogs
import win32evtlogutil

logs = windowslogs.get_event_logs('localhost', 'system', {'EventID': []})

for l in logs:
    print l
