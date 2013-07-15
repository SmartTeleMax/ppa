# $Id: Caches.py,v 1.1.1.1 2004/04/09 13:18:10 ods Exp $
# TODO: LimitedMemoryCache (limits number of objects in memory), BSDDBCache,
# NestedCaches (e.g.: NestedCaches(LimitedMemoryCache, BSDDBCache) stores
# a limited number of templates in memory and all the rest in BSDDB).
#
# XXX Timestamp control for reloading? We may need it even for memory cache if
# we want use 'em in long running custom server or under mod_python.
# XXX Timestamp control should be in separate class! It's interesting to use
# nested LimitedMemoryCache without reloading and BSDDBCache (SQLCache?) with
# reloading.
# XXX We need filename to stat or callback method recieved by controller from
# source finder.
# XXX We need reference to Controller (or SourceFinder?) to reload? Or just
# raise NotCached if stats changed?


class NotCached(LookupError): pass


class DummyCache:

    def store(self, key, object):
        pass

    def retrieve(self, key):
        raise NotCached(key)


class MemoryCache:

    def __init__(self, data={}):
        self._cache = {}
        self._types = {}
        for (name, type), object in data.iteritems():
            self.store((name, type), object)

    def store(self, (name, type), object):
        self._cache[name, type] = object
        self._types[name] = type

    def retrieve(self, (name, type)):
        if type is None:
            if not self._types.has_key(name):
                raise NotCached((name, type))
            return self._cache[name, self._types[name]]
        elif not self._cache.has_key((name, type)):
            raise NotCached((name, type))
        else:
            return self._cache[name, type]

    def clear(self):
        self._cache.clear()
        self._types.clear()
