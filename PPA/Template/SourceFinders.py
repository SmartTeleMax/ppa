# $Id: SourceFinders.py,v 1.5 2003/11/25 12:08:52 ods Exp $

from glob import glob
import os


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


# XXX Should the finder know about where to get enginesByType? I guess no. We
# may replace None with full list of types we can handle. This is much more
# flexible!
class FileSourceFinder:
    '''Find source of template by name and type.'''

    def __init__(self, search_dirs, file=file):
        self._search_dirs = search_dirs
        self._file = file
    
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
            for file in files:
                name, ext = os.path.splitext(file)
                if os.path.basename(name)==template_basename:
                    ext = ext[1:]
                    # We should check the type to avoid backups at least
                    if enginesByType.has_key(ext):
                        return self._file(file), ext
        else:
            raise TemplateNotFoundError(template_name, template_type,
                                        ', '.join(self._search_dirs))
