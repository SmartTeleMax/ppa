# $Id: XMLTAL.py,v 1.3 2004/04/12 10:02:38 ods Exp $

import _TALCommon
from TAL.TALParser import TALParser
from TAL.XMLParser import XMLParser
from TAL.TALGenerator import TALGenerator
from TAL.TALDefs import XML_NS

# XXX zLOG module is outside of TAL -- need some hacks.
try:
    import zLOG
except ImportError:
    import sys, new
    zLOG = new.module('zLOG')
    zLOG.LOG = lambda *args: None
    zLOG.INFO = zLOG.PROBLEM = None
    sys.modules['zLOG'] = zLOG


class Engine(_TALCommon.Engine):

    type = 'xtal'
    class _parser_class(TALParser):
        def __init__(self, gen, encoding=None):
            XMLParser.__init__(self, encoding=encoding)
            self.gen = gen
            self.nsStack = []
            self.nsDict = {XML_NS: 'xml'}
            self.nsNew = []
    
    def compileString(self, source, template_name, get_template):
        cengine = _TALCommon.Compiler()
        generator = TALGenerator(cengine, self._xml)
        if isinstance(source, unicode):
            parser = self._parser_class(generator, encoding='utf-8')
            parser.parseString(source.encode('utf-8'))
        else:
            parser = self._parser_class(generator)
            parser.parseString(source)
        return parser.getCode()
