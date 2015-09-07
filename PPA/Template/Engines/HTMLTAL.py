import _TALCommon


class Engine(_TALCommon.Engine):

    type = 'htal'
    _xml = 0
    from TAL.HTMLTALParser import HTMLTALParser as _parser_class
