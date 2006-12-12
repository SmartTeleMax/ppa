"""PPA.Template - templating support in PPA.

This package defines a set of classes to find, interpret and evaluate templates
in varuois templating languages.

You may look deeper in code to use all provided classes directly, but more
common usage is like this:

# PPA.Template namespace provides two classes:
# FileTemplateGetter - finds template in filesystem directories
# StringTemplateGetter - is initialized with template body and uses it as onerous template

from PPA.Template import *

# Example usage of FileTemplateGetter:

# initialize FileTemplateGetter to find templates in files on filesystem
getter = FileTemplateGetter(
    ['/home/project/templates', '/var/common_templates'])
# ask getter to find template by name
template = getter('site_index_page')
# render template, namespace is given as keyword arguments
rendered_data = template(site_title='My site')

# Example usage of StringTemplateGetter:

# initialize StringTemplateGetter with template source
getter = StringTemplateGetter('My name is <%= name %>')
# NOTE: second param, template_type is required by StringTemplateGetter
template = getter('dummy template name', 'pyem')
rendered_data = template(name='Variable')
"""

import sys
import Controller, SourceFinders
from Caches import MemoryCache
from Engines import EngineImporter

__all__ = ['FileTemplateGetter', 'StringTemplateGetter']


class _Writer:
    """Fast, but incompatible StringIO.StringIO implementation. Only supports
    write and getvalue methods"""
    
    def __init__(self):
	self.parts = []
	self.write = self.parts.append
    
    def getvalue(self):
	return ''.join(self.parts)


class TemplateWrapper(Controller.TemplateWrapper):

    def __call__(self, namespace={}, **kwargs):
        fp = _Writer()
        self.interpret(fp, namespace, kwargs)
        return fp.getvalue()


class TemplateGetter:
    """Base template getter class, is not used directly.

    Common usage is:

    getter = TemplateGeatter()
    template = getter('template_name')
    """

    def __init__(self, source_finder, cache=MemoryCache()):
	self.controller = Controller.TemplateController(
            source_finder,
            template_wrapper_class=TemplateWrapper,
            template_cache=cache)

    def __call__(self, template_name, template_type=None):
        return self.controller.getTemplate(template_name, template_type)

	
class FileTemplateGetter(TemplateGetter):
    """Gets template from filesystem. Is initialized with list of
    filesystem directories where templates are searched.

    Usage:

    getter = FileTemplateGetter(['dir1', 'dir2'])
    template = getter('template_name')
    """

    def __init__(self, dirs, *args, **kwargs):
	source_finder = SourceFinders.FileSourceFinder(dirs)
	TemplateGetter.__init__(self, source_finder, *args, **kwargs)


class StringTemplateGetter(TemplateGetter):
    """Is initialized with template body, and returns it as template.

    Usage:

    getter = StringTemplateGetter(template_source)
    template = getter('template_name', 'template_type')

    Param template_type is mandatory for StringTemplateGetter.__call__()
    """

    def __init__(self, template_source, *args, **kwargs):
	source_finder = SourceFinders.StringSourceFinder(template_source)
	TemplateGetter.__init__(self, source_finder, *args, **kwargs)

    def __call__(self, template_name, template_type):
        """template_type is mandatory for StringTemplateGetter.__call__"""
        return TemplateGetter.__call__(self, template_name, template_type)


if __name__ == '__main__':
    getter = FileTemplateGetter(['/tmp'])
    template = getter('templatename')
    data = template(name='test')
    print data
    
    getter = StringTemplateGetter('name is <%= name %>')
    template = getter('sometemplate', 'pyem')
    print template(name='test')
    
