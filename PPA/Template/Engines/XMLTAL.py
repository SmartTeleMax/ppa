# $Id: XMLTAL.py,v 1.1.1.1 2004/04/09 13:18:11 ods Exp $

import _TALCommon
from TAL.TALParser import TALParser
from TAL.XMLParser import XMLParser
from TAL.TALGenerator import TALGenerator
from TAL.TALDefs import XML_NS


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
