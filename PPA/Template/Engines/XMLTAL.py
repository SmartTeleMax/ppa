# $Id: XMLTAL.py,v 1.3 2003/11/25 12:08:52 ods Exp $

import _TALCommon


# XXX zLOG module is outside of TAL -- need some hacks.
import sys, new
zLOG = new.module('zLOG')
zLOG.LOG = lambda *args: None
zLOG.INFO = zLOG.PROBLEM = None
sys.modules['zLOG'] = zLOG



class Engine(_TALCommon.Engine):

    type = 'xtal'
    from TAL.TALParser import TALParser as _parser_class
