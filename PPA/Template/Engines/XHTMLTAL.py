# $Id: XHTMLTAL.py,v 1.2 2003/11/25 12:08:52 ods Exp $

import _TALCommon


class Engine(_TALCommon.Engine):

    type = 'xhtal'
    _xml = 1
    from TAL.HTMLTALParser import HTMLTALParser as _parser_class
