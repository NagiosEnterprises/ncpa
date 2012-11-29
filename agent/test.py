#!/usr/bin/env python

import unittest

class ReturnObjectTestCase(unittest.TestCase):
    
    def setUp(self):
        from processor import ReturnObject
        self.returnObject = ReturnObject()
        testRange = xrange(-50,50)
        self.testRanges = (
            {   'trange'   : '',
                'testvals' : testRange,
                'expected' : [ False for x in testRange ],
                },
            {   'trange'   : '10',
                'testvals' : testRange,
                'expected' : [ 0 >= x or x >= 10 for x in testRange ],
                },
            {   'trange'   : '10:',
                'testvals' : testRange,
                'expected' : [ x < 10 for x in testRange ],
                },
            {   'trange'   : '~:10',
                'testvals' : testRange,
                'expected' : [ x > 10 for x in testRange ],
                },
            {   'trange'   : '10:20',
                'testvals' : testRange,
                'expected' : [ x < 10 or x > 20 for x in testRange ],
                },
            {   'trange'   : '@10:20',
                'testvals' : testRange,
                'expected' : [ x >= 10 and x <= 20 for x in testRange ],
                },
            ) # Close test definition ranges
    
    def tearDown(self):
        self.returnObject = None
    
    def test_is_within_range(self):
        for testRange in self.testRanges:
            trange = testRange['trange']
            testvals = testRange['testvals']
            expected = testRange['expected']
            for test,expect in zip(testvals, expected):
                test_result = self.returnObject.is_within_range(trange, test)
                self.assertEqual(test_result, expect, 'Failed on range %s, Input: %s, Expected: %s, Actual: %s' % (trange, str(test), expect, test_result ))

if __name__ == "__main__":
    unittest.main()
