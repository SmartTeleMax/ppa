#!/usr/bin/env python
# $Id: testCaches.py,v 1.1.1.1 2004/04/09 13:18:11 ods Exp $

import unittest, sys

sys.path.insert(0, '..')

from PPA.Template.Caches import NotCached, DummyCache, MemoryCache

class DummyTemplate:
    '''Defines interface cache classes should rely on'''

    def __init__(self, template_id):
        self._template_id = template_id

    # We need it to verify template is the same
    def __cmp__(self, other):
        return cmp(self._template_id, other._template_id)

    # XXX serialization

class DummyCacheTest(unittest.TestCase):

    def testEmpty(self):
        '''Retrieve from empty DummyCache'''
        cache = DummyCache()
        self.assertRaises(NotCached, cache.retrieve, ('name', 'type'))

    def testStoreRetrieve(self):
        '''Store-retrieve cycle of DummyCache'''
        cache = DummyCache()
        cache.store(('name', 'type'), DummyTemplate(''))
        self.assertRaises(NotCached, cache.retrieve, ('name', 'type'))


class MemoryCacheTest(unittest.TestCase):

    def testEmpty(self):
        '''Retrieve from empty MemoryCache'''
        cache = MemoryCache()
        self.assertRaises(NotCached, cache.retrieve, ('name', 'type'))

    def testStoreRetrieve(self):
        '''Store-retrieve cycle of MemoryCache'''
        cache = MemoryCache()
        template = DummyTemplate('')
        cache.store(('name', 'type'), template)
        self.assertEqual(cache.retrieve(('name', 'type')), template)
        self.assertEqual(cache.retrieve(('name', None)), template)

    def testPreinit(self):
        '''Retrieve from pre-inited MemoryCache'''
        template = DummyTemplate('')
        cache = MemoryCache({('name', 'type'): template})
        self.assertEqual(cache.retrieve(('name', 'type')), template)
        self.assertEqual(cache.retrieve(('name', None)), template)

    def testTheSame(self):
        '''Store many - retrieve & compare for MemoryCache'''
        cache = MemoryCache()
        templates = {}
        for i in range(10):
            templates[i] = DummyTemplate(i)
            cache.store(('name%s' % i, 'type%s' % i), templates[i])
        for i in range(0, 10, 2)+range(1, 10, 2):
            self.assertRaises(NotCached, cache.retrieve, ('name%s', 'type1'))
            self.assertEqual(cache.retrieve(('name%s' % i, None)),
                             templates[i])
            self.assertEqual(cache.retrieve(('name%s' % i, 'type%s' % i)),
                             templates[i])

    def testClear(self):
        '''MemoryCache.clear()'''
        cache = MemoryCache()
        template = DummyTemplate(1)
        cache.store(('name', 'type'), template)
        cache.clear()
        self.assertRaises(NotCached, cache.retrieve, ('name', 'type'))
        self.assertRaises(NotCached, cache.retrieve, ('name', None))
        template = DummyTemplate(2)
        cache.store(('name', 'type'), template)
        self.assertEqual(cache.retrieve(('name', 'type')), template)
        self.assertEqual(cache.retrieve(('name', None)), template)
            


def testSuite():

    return unittest.TestSuite([unittest.makeSuite(DummyCacheTest),
                               unittest.makeSuite(MemoryCacheTest)])


if __name__=='__main__':
    unittest.TextTestRunner().run(testSuite())
