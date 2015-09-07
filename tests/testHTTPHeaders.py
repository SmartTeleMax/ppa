#!/usr/bin/env python

import unittest, sys, os

dir = os.path.dirname(os.path.abspath(globals().get('__file__', sys.argv[0])))
sys.path.insert(0, os.path.dirname(dir))

from PPA.HTTP.Adapters.Base import Headers

class HeadersTest(unittest.TestCase):

    def assertSameItems(self, seq1, seq2):
        self.assertEqual(len(seq1), len(seq2))
        for item in seq1:
            self.failUnless(item in seq2)

    def testInitStr(self):
        '''Headers.__init__, Headers.__str__'''
        h = Headers({'key': 'value'})
        self.assertEqual(str(h), 'key: value\r\n')
        h = Headers({'Key': 'Value'})
        self.assertEqual(str(h), 'Key: Value\r\n')
        h = Headers({'key1': 'value1', 'key2': 'value2'})
        self.failUnless(str(h) in ['key1: value1\r\nkey2: value2\r\n',
                                   'key2: value2\r\nkey1: value1\r\n'])
        h = Headers([('key1', 'value1'), ('key2', 'value2')])
        self.assertEqual(str(h), 'key1: value1\r\nkey2: value2\r\n')
        h = Headers([('key', 'value1'), ('key', 'value2')])
        self.assertEqual(str(h), 'key: value1\r\nkey: value2\r\n')

    def testAdd(self):
        '''Headers.add'''
        h = Headers({'key1': 'value1'})
        self.assertEqual(len(h), 1)
        self.assertEqual(h.keys(), ['key1'])
        h.add('key2', 'value2')
        self.assertEqual(len(h), 2)
        self.assertSameItems(h.keys(), ['key1', 'key2'])
        h.add('Key1', 'value2')
        self.assertEqual(len(h), 3)
        self.assertSameItems(h.keys(), ['key1', 'key2'])

    def testGetSet(self):
        '''Getting/setting/deleting item in Headers'''
        h = Headers([('key1', 'value1'),
                     ('key2', 'value2'),
                     ('KEY1', 'VALUE1')])
        self.assertEqual(len(h), 3)
        self.assertSameItems(h.keys(), ['key1', 'key2'])
        self.assertEqual(h['key2'], 'value2')
        self.assertEqual(h['key1'], 'value1, VALUE1')
        h['KEY2'] = 'Value2'
        self.assertEqual(len(h), 3)
        self.assertSameItems(h.keys(), ['key1', 'key2'])
        self.assertEqual(h['key2'], 'Value2')
        h['key1'] = 'Value1'
        self.assertEqual(len(h), 2)
        self.assertSameItems(h.keys(), ['key1', 'key2'])
        self.assertEqual(h['key1'], 'Value1')


def testSuite():

    return unittest.makeSuite(HeadersTest)


if __name__=='__main__':
    unittest.TextTestRunner().run(testSuite())
