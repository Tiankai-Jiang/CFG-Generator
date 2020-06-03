import tokenize, io, sys, autopep8, re

nodeID = 1

class Node:

    def __init__(self):
        self.ID = nodeID
        nodeID += 1
        self.content = ''
        self.TO = []

class G:

    def __init__(self, name):
        self.name = name
        start = Node()
        start.content = 'start'
        self.nodes = [start]

class PyParser:

    def __init__(self, script):
        self.script = script

    def formatCode(self):
        self.script = autopep8.fix_code(self.script)

    # https://github.com/liftoff/pyminifier/blob/master/pyminifier/minification.py
    def removeCommentsAndDocstrings(self):
        io_obj = io.StringIO(self.script) # ByteIO for Python2?
        out = ""
        prev_toktype = tokenize.INDENT
        last_lineno = -1
        last_col = 0
        for tok in tokenize.generate_tokens(io_obj.readline):
            token_type = tok[0]
            token_string = tok[1]
            start_line, start_col = tok[2]
            end_line, end_col = tok[3]
            if start_line > last_lineno:
                last_col = 0
            if start_col > last_col:
                out += (" " * (start_col - last_col))
            # Remove comments:
            if token_type == tokenize.COMMENT:     
                pass
            # This series of conditionals removes docstrings:
            elif token_type == tokenize.STRING:
                if prev_toktype != tokenize.INDENT:
            # This is likely a docstring; double-check we're not inside an operator:
                    if prev_toktype != tokenize.NEWLINE:
                        # Note regarding NEWLINE vs NL: The tokenize module
                        # differentiates between newlines that start a new statement
                        # and newlines inside of operators such as parens, brackes,
                        # and curly braces.  Newlines inside of operators are
                        # NEWLINE and newlines that start new code are NL.
                        # Catch whole-module docstrings:
                        if start_col > 0:
                            # Unlabelled indentation means we're inside an operator
                            out += token_string
                        # Note regarding the INDENT token: The tokenize module does
                        # not label indentation inside of an operator (parens,
                        # brackets, and curly braces) as actual indentation.
                        # For example:
                        # def foo():
                        #     "The spaces before this docstring are tokenize.INDENT"
                        #     test = [
                        #         "The spaces before this string do not get a token"
                        #     ]
            else:
                out += token_string
            prev_toktype = token_type
            last_col = end_col
            last_lineno = end_line
        self.script = out

    # TODO: this method will also remove empty lines in a multiline string
    # However, it does not affect the control flow
    def removeBlankLines(self):
        io_obj = io.StringIO(self.script)
        self.script = "".join([a for a in io_obj.readlines() if a.strip()])

    
    # Remove multiline code (lines that end with \) ensures that 
    # All indentations outside of brackets will be in the same line
    # which makes it easier to analyse the control flow
    def removeMultiLineCode(self):
        io_obj = io.StringIO(self.script)
        lines = [a for a in io_obj.readlines() if a.strip()]
        for i in reversed(range(len(lines)-1)):
            if(lines[i].rstrip().endswith('\\')):
                lines[i] = lines[i][:-2] + lines[i+1].lstrip()
                lines[i+1] = ''
        self.script = "".join([a for a in lines if a.strip()])

    def extractScope(self):
        pass

    def removeLeadingIndent(self, lines):
        spaceCount = 0
        for i in range(len(lines[0])):
            if(lines[0][i]==' '):
                spaceCount += 1
            else:
                break
        for i in range(len(lines)):
            lines[i] = lines[i][spaceCount:]
        return lines

    def getIndentLevel(self, lines):
        pass

    def getFuncName(self, s):
        m = re.search(r'def\s(.*):', s)
        return m.groups()[0]

    def generateCFG(self, scope):
        io_obj = io.StringIO(self.script)
        lines = [a for a in io_obj.readlines()]
        funcLines = self.removeLeadingIndent([lines[x] for x in scope])
        g = G(getFuncName(funcLines[0]))
        


if __name__ == '__main__':
    filename = sys.argv[1]
    source = open(filename, 'r').read() + '\n'
    try:
        compile(source, filename, 'exec')
    except:
        print('Error in source code')
        exit(1)

    parser = PyParser(source)
    parser.removeCommentsAndDocstrings()
    parser.formatCode()
    parser.removeBlankLines()
    parser.removeMultiLineCode()
    print(parser.script, end = '')