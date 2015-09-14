# $Id: XHTMLTAL.py,v 1.1.1.1 2004/04/09 13:18:11 ods Exp $

import _TALCommon


class Engine(_TALCommon.Engine):

    type = 'xhtal'
    _xml = 1
    from TAL.HTMLTALParser import HTMLTALParser as _parser_class
