# $Id: PythonEmbedded.py,v 1.3 2004/04/09 16:26:14 ods Exp $

import string, re

single_re = r"'[^\n'\\]*(?:\\.[^\n'\\]*)*'"
double_re = r'"[^\n"\\]*(?:\\.[^\n"\\]*)*"'
triple_single_re = r"'''[^'\\]*(?:(?:\\.|'(?!''))[^'\\]*)*'''"
triple_double_re = r'"""[^"\\]*(?:(?:\\.|"(?!""))[^"\\]*)*"""'
string_re = r'(%s|%s|%s|%s)' % (triple_single_re, triple_double_re,
                                single_re, double_re)

expr_match = re.compile(r'(?:[^\'"%%\n]|%%(?!>)|\\.|%s)+' % string_re,
                        re.S).match
suite_match = re.compile(r'(?:[^\'"%%]|%%(?!>)|\\.|%s)*' % string_re,
                         re.S).match
suite_check_start = re.compile(r'\s*\n').match
suite_check_end = re.compile(r'\n\s*$').search


class Error(Exception):
    def __init__(self, message='', filename='?', line=None):
        self.message = message
        self.filename = filename
        self.line = line
    def __str__(self):
        res = '%s in "%s"' % (self.message, self.filename)
        if self.line:
            res = '%s, line %d' % (res, self.line)
        return res

class ParseError(Error): pass
class CompileError(Error): pass


class Parser:
    
    def __init__(self, s, filename='?'):
        self.string = s
        self.filename = filename
        self.length = len(self.string)
    
    def process(self):
        self.cur_pos = 0
        self.parts = []
        state = 'html'
        while state!='EOF':
            state = getattr(self, 'process_'+state)()
        return self.parts

    def append(self, (state, s)):
        #print '===', state, '==='
        #print s
        self.parts.append((state, s))
    
    def report_error(self, message, pos=None):
        if pos is None:
            pos = self.cur_pos
        line = self.string.count('\n', 0, pos) + 1
        raise ParseError(message, self.filename, line)
    
    def process_html(self):
        pos = self.string.find('<%', self.cur_pos)
        if pos<0:
            text = self.string[self.cur_pos:]
            if text:
                self.append(('html', text))
            return 'EOF'
        text = self.string[self.cur_pos:pos]
        if text:
            self.append(('html', text))
        if self.string[pos+2:pos+3]=='=':
            self.cur_pos = pos+3
            return 'expr'
        else:
            self.cur_pos = pos+2
            return 'suite'

    def process_expr(self):
        m = expr_match(self.string, self.cur_pos)
        if not m:
            self.report_error('Empty expression')
        pos = m.end()
        text = self.string[self.cur_pos:pos].strip()
        if not text:
            self.report_error('Empty expression')
        self.append(('expr', text))
        if self.length==pos:
            self.report_error('Unexpected EOF in embedded expression', pos)
        if self.string[pos:pos+2]!='%>':
            self.report_error('Embedded expression should end with "%>"', pos)
        self.cur_pos = pos+2
        return 'html'

    def process_suite(self):
        m = suite_match(self.string, self.cur_pos)
        assert m
        pos = m.end()
        suite = self.string[self.cur_pos:pos]
        if not suite_check_start(suite):
            self.report_error(
                'Embedded suite must start from new line after "...<%"',
                self.cur_pos)
        if not suite_check_end(suite):
            self.report_error(
                'Embedded suite must end with separate line containing "%>..."',
                pos)
        self.append(('suite', suite))
        if self.length==pos:
            self.report_error('Unexpected EOF in embedded suite', pos)
        assert self.string[pos:pos+2]=='%>', [self.string[pos:]]
        self.cur_pos = pos+2
        return 'html'

def _compile(source, filename, method):
    """Python built in function compile has some problems (rather person
    who uses compile() has this problems) with unicode source.

    This function makes compiling unicode source possible.

    NOTE: _compile is depended on undocumented python intepreter features
    which behavior may change in future. At the moment _compile works well
    with up to python2.4

    NOTE: _compile is a performance hit, but at the moment i dont know how
    to deal with situation in other ways."""

    unicodeStringCharset = "utf-8"

    def decode(obj, charset=unicodeStringCharset):
        if type(obj) is str:
            try:
                obj.decode('ascii')
            except UnicodeError: # UnicodeDecodeError
                obj = obj.decode(unicodeStringCharset)
        elif type(obj) is tuple:
            # python2.4 add tuples to code.co_const, tuples may contain
            # broken utf-8 strings too, so we have to decode them recursively
            obj = tuple([decode(i) for i in obj])
        return obj

    code = compile(source, filename, method)
    if type(source) is unicode:
        # when compiling unicode source compile() encodes all const strings
        # with utf-8. client provided unicode source is supposed to get
        # all const back as unicode. Following code decodes consts back to
        # unicode
        consts = [decode(i) for i in code.co_consts]
        import new
        code = new.code(code.co_argcount, code.co_nlocals,
                        code.co_stacksize, code.co_flags, code.co_code,
                        tuple(consts), code.co_names, code.co_varnames,
                        code.co_filename, code.co_name,
                        code.co_firstlineno, code.co_lnotab)
    return code
    

class Compiler:

    def __init__(self, source, filename):
        self.source = source
        self.filename = filename
        
    def process(self):
        parser = Parser(self.source, self.filename)
        self.content = content = []
        self.write = write = self.content.append
        for state, s in parser.process():
            if content and content[-1]:
                if content[-1][-1] not in ' \n\t;':
                    write('; ')
            getattr(self, 'process_'+state)(s)
        content.append('\n')
        source = ''.join(content)
        try:
            return _compile(source, self.filename, 'exec')
        except SyntaxError, exc:
            raise CompileError(exc.msg, self.filename, exc.lineno)

    def process_html(self, s):
        self.write('__PythonEmbedded_write__("""%s""");' % \
                   s.replace('"', '\\"'))

    def process_expr(self, s):
        self.write('__PythonEmbedded_write__(%s);' % s)

    def process_suite(self, s):
        self.write(s)


class Writer:
    def __init__(self, fp):
        self.fp = fp
    def __call__(self, object):
        self.fp.write('%s' % (object,))


class Engine:

    type = 'pyem'
        
    def compileString(self, source, template_name, get_template):
        c = Compiler(source, '.'.join((template_name, self.type)))
        return c.process()
    
    def compileFile(self, fp, template_name, get_template):
        return self.compileString(fp.read(), template_name, get_template)

    def interpret(self, program, fp, globals, locals, get_template):
        if fp is None:
            import sys
            fp = sys.stdout
        globals['__PythonEmbedded_write__'] = Writer(fp)
        exec program in globals, locals

    def dump(self, program):
        from marshal import dumps
        return dumps(program)

    def load(self, s):
        from marshal import loads
        return loads(s)
