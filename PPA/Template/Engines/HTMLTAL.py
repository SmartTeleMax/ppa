# $Id: HTMLTAL.py,v 1.8 2003/11/25 12:08:52 ods Exp $

import _TALCommon


class Engine(_TALCommon.Engine):

    type = 'htal'
    _xml = 0
    from TAL.HTMLTALParser import HTMLTALParser as _parser_class
