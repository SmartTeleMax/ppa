#!/usr/bin/env python
# $Id: testSourceFinders.py,v 1.2 2004/04/09 15:48:36 ods Exp $

import unittest, sys, os

dir = os.path.dirname(os.path.abspath(globals().get('__file__', sys.argv[0])))
sys.path.insert(0, os.path.dirname(dir))

class FileSourceFinderTest(unittest.TestCase):

    class _HackedGlob:
        def __init__(self, type):
            self.type = type
        def __call__(self, pattern):
            res = []
            for repl in ('part.'+self.type, self.type):
                res.append(pattern.replace('*', repl))
            return res

    class _HackedFile:
        def __init__(self, file, mode='r'):
            self.file = file
            self.mode = mode

    def testFind(self):
        '''FileSourceFinder.find()'''
        # There were two bugs in FileSourceFinder that is difficult to
        # reproduce.
        # This code looks ugly, can we do it better way?
        from PPA.Template.Engines import enginesByType
        type = enginesByType.keys()[0]
        # Save environment
        from PPA.Template import SourceFinders
        real_glob = SourceFinders.glob
        SourceFinders.glob = self._HackedGlob(type)
        import __builtin__
        # test
        sf = SourceFinders.FileSourceFinder(['/dir'], self._HackedFile)
        self.assertEqual(sf.find('test')[0].file,
                         '/dir/test.'+type)
        self.assertEqual(sf.find('test1.test2')[0].file,
                         '/dir/test1.test2.'+type)
        self.assertEqual(sf.find('test1/test2')[0].file,
                         '/dir/test1/test2.'+type)
        self.assertEqual(sf.find('test1/test2.test3')[0].file,
                         '/dir/test1/test2.test3.'+type)
        # Restore environment
        SourceFinders.glob =  real_glob
        SourceFinders.__builtins__ = __builtin__


def testSuite():

    return unittest.TestSuite([unittest.makeSuite(FileSourceFinderTest)])


if __name__=='__main__':
    unittest.TextTestRunner().run(testSuite())
