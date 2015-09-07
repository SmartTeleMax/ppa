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


class TemplateDirectory(str):
    '''Incapsulates directory name and charset of files within it'''

    def __new__(cls, directory, charset=None):
        inst = str.__new__(cls, directory)
        inst.charset = charset
        return inst

    def getReader(self, file_name):
        fp = open(file_name, 'rb')
        if self.charset:
            return codecs.getreader(self.charset)(fp)
        else:
            return fp


class SourceFinder:
    """Template finder. Usage is:

    finder = SomeSourceFinder()
    fp, template_type = finder.find("templatename")
    fp, template_type = finder.find("templatename", "pyem")
    """

    def find(self, template_name, template_type=None):
        """Returns tuple (fp, template_type), where fp is file object
        of template body"""
        raise NotImplementedError()


class DummySourceFinder(SourceFinder):
    '''Usefull when we need only ready to use templates in cache'''

    def find(self, template_name, template_type=None):
        raise TemplateNotFoundError(template_name, template_type, 'cache')


class ChainSourceFinder(SourceFinder):

    def __init__(self, *args):
        self._finders = args

    def find(self, template_name, template_type=None):
        where = []
        for finder in self._finders:
            try:
                return finder.find(template_name, template_type)
            except TemplateNotFoundError, exc:
                where.append(exc.where)
        raise TemplateNotFoundError(template_name, template_type,
                                    ', '.join(where))


class FileSourceFinder(SourceFinder):
    '''Find source of template by name and type in filesystem directory.
    Must be initialized with list of filesystem directories where to find
    templates.

    finder = FileSourceFinder(["template_dir1", "template_dir2"])
    '''

    def __init__(self, search_dirs, engines_by_type=None):
        """search_dirs is a list of TemplateDirectory instances,
        engines_by_type is an optional mapping of engine types to modules."""
        self._search_dirs = []
        for dir in search_dirs:
            if not isinstance(dir, TemplateDirectory):
                dir = TemplateDirectory(dir)
            self._search_dirs.append(dir)
        if engines_by_type is None:
            from Engines import enginesByType as engines_by_type
        self._engines_by_type = engines_by_type

    def find(self, template_name, template_type=None):
        if template_type is None:
            pathern = template_name+'.*'
        else:
            pathern = '.'.join((template_name, template_type))
        template_basename = os.path.basename(template_name)
        for dir in self._search_dirs:
            path = os.path.join(dir, pathern)
            for file_name in glob(path):
                name, ext = os.path.splitext(file_name)
                if os.path.basename(name)==template_basename:
                    template_type = ext[1:]
                    # We should check the type to avoid backups at least
                    if self._engines_by_type.has_key(template_type):
                        assert isinstance(dir, TemplateDirectory), \
                               "Source dir %r is not an instance of " \
                               "TemplateDirectory" % dir
                        return dir.getReader(file_name), template_type
        else:
            raise TemplateNotFoundError(template_name, template_type,
                                        ', '.join(self._search_dirs))

