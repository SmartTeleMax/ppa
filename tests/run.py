#!/usr/bin/env python

from glob import glob
import os, sys, unittest


def testSuite():
    suite = unittest.TestSuite()
    dir = os.path.dirname(globals().get('__file__', sys.argv[0]))
    for test_file in glob(os.path.join(dir, 'test?*.py')):
        module_name = os.path.splitext(os.path.basename(test_file))[0]
        module = __import__(module_name)
        suite.addTest(module.testSuite())
    return suite

if __name__=='__main__':
    unittest.TextTestRunner().run(testSuite())
