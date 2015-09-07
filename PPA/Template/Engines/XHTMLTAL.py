import _TALCommon


class Engine(_TALCommon.Engine):

    type = 'xhtal'
    _xml = 1
    from TAL.HTMLTALParser import HTMLTALParser as _parser_class
