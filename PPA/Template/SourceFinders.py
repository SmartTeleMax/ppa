# $Id: SourceFinders.py,v 1.1.1.1 2004/04/09 13:18:10 ods Exp $

from glob import glob
import os, codecs


class TemplateNotFoundError(Exception):
    def __init__(self, name, type=None, where=None):
        self.name = name
        self.type = type
        self.where = where
    def __str__(self):
        msg = '"%s"' % self.name
        if self.type is not None:
            msg = '%s of type "%s"' % (msg, self.type)
        if self.where is not None:
            msg = ' in '.join((msg, self.where))
        return msg


class DummySourceFinder:
    '''Usefull when we need only ready to use templates in cache'''

    def find(self, template_name, template_type=None):
        raise TemplateNotFoundError(template_name, template_type, 'cache')


class TemplateDirectory(str):
    '''Incapsulates directory name and charset of files within it'''
    
    def __new__(cls, directory, charset=None):
        inst = str.__new__(cls, directory)
        inst.charset = charset
        return inst

    def getReader(self, file):
        if self.charset:
            return codecs.getreader(self.charset)(file)
        else:
            return file
        

# XXX Should the finder know about where to get enginesByType? I guess no. We
# may replace None with full list of types we can handle. This is much more
# flexible!
class FileSourceFinder:
    '''Find source of template by name and type.'''

    def __init__(self, search_dirs):
        """search_dirs is a list of TemplateDirectory instances"""
        self._search_dirs = search_dirs
    
    def find(self, template_name, template_type=None):
        from Engines import enginesByType
        if template_type is None:
            pathern = template_name+'.*'
        else:
            pathern = '.'.join((template_name, template_type))
        template_basename = os.path.basename(template_name)
        for dir in self._search_dirs:
            path = os.path.join(dir, pathern)
            files = glob(path)
            for filename in files:
                name, ext = os.path.splitext(filename)
                if os.path.basename(name)==template_basename:
                    ext = ext[1:]
                    # We should check the type to avoid backups at least
                    if enginesByType.has_key(ext):
                        assert isinstance(dir, TemplateDirectory), \
                               "Source dir %r is not an instance of " \
                               "TemplateDirectory" % dir
                        return dir.getReader(file(filename)), ext
        else:
            raise TemplateNotFoundError(template_name, template_type,
                                        ', '.join(self._search_dirs))
