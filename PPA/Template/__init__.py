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

__all__ = ['fromString', 'fromFile']


_controller = None

def fromString(source, template_type, encoding=None, template_name='?',
               controller=None):
    global _controller
    if controller is None:
        if _controller is None:
            _controller = Controller.TemplateController()
        controller = _controller
    return controller.compileString(source, template_type, template_name)

def fromFile(source_fp, template_type, encoding=None, template_name='?',
               controller=None):
    global _controller
    if controller is None:
        if _controller is None:
            _controller = Controller.TemplateController()
        controller = _controller
    return controller.compileFile(source_fp, template_type, template_name)

def filesControllerXXXBetterName(dirs, **kwargs):
    source_finder = SourceFinders.FileSourceFinder(dirs)
    return Controller.TemplateController(source_finder, **kwargs)
