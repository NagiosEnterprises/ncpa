#!/usr/bin/env python

import wmi
import sys
import pythoncom
import netsyslog
import unittest
import logging

def wait_for_next_log():
    pythoncom.CoInitialize()
    c = wmi.WMI()
    w = c.watch_for(notification_type='Creation', wmi_class='Win32_NTLogEvent')
    event = w()
    print((event.wmi_property()))
    #~ logging.debug('%s in %s log: %s' % (event.Type, event.Logfile, event.Message)

def translate_level_to_syslog(event):
    '''Returns the syslog code for the given event log.'''
    assert isinstance(event, str)
    
    translations = {    'Error'         : 3,
                        'Verbose'       : 7,
                        'Informational' : 6,
                        'Critical'      : 1,
                        'Critical Error': 0,
                        'Warning'       : 4
                    }
    
    try:
        translated = translations[event]
    except KeyError as e:
        logging.exception(e)
        translated = 0
    
    assert isinstance(translated, int)
    return translated

class WELFTests(unittest.TestCase):
    
    def test_translate_level_to_syslog(self):
        result = translate_level_to_syslog('Error')
        self.assertTrue(isinstance(result, int))
        
        result = translate_level_to_syslog('Not In Dictionary')
        self.assertTrue(isinstance(result, int))

if __name__ == "__main__":
    try:
        if sys.argv[1] == 'run':
            wait_for_next_log()
    except IndexError:
        unittest.main()
