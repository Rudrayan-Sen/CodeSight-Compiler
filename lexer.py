import re

class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, Line: {self.line}, Col: {self.column})"

class Lexer:
    # Pattern definitions
    KEYWORDS = {'int', 'float', 'if', 'else', 'while', 'return', 'print'}
    
    # Combined regex pattern for all tokens
    # Note: Order matters! FLOAT_CONST before INT_CONST, longer operators before shorter ones.
    TOKEN_REGEX = [
        ('FLOAT_CONST', r'\d+\.\d+'),
        ('INT_CONST',   r'\d+'),
        ('IDENTIFIER',  r'[a-zA-Z_]\w*'),
        ('OPERATOR',    r'==|!=|<=|>=|&&|\|\||[+\-*/=<>]'),
        ('DELIMITER',   r'[(){};,]'),
        ('WHITESPACE',  r'[ \t]+'),
        ('NEWLINE',     r'\n'),
        ('MISMATCH',    r'.') # Any other character
    ]
    
    def __init__(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.errors = []
        self._compile_regex()

    def _compile_regex(self):
        parts = []
        for name, pattern in self.TOKEN_REGEX:
            parts.append(f'(?P<{name}>{pattern})')
        self.regex = re.compile('|'.join(parts))

    def tokenize(self):
        self.tokens = []
        self.errors = []
        line_num = 1
        line_start = 0
        
        for match in self.regex.finditer(self.source_code):
            kind = match.lastgroup
            value = match.group()
            column = match.start() - line_start + 1
            
            if kind == 'NEWLINE':
                line_start = match.end()
                line_num += 1
            elif kind == 'WHITESPACE':
                continue
            elif kind == 'MISMATCH':
                self.errors.append(f"Lexical Error at line {line_num}, col {column}: Invalid character '{value}'")
                self.tokens.append(Token('ERROR', value, line_num, column))
            else:
                if kind == 'IDENTIFIER' and value in self.KEYWORDS:
                    kind = 'KEYWORD'
                
                # Conversion to correct types if necessary
                if kind == 'INT_CONST':
                    value = int(value)
                elif kind == 'FLOAT_CONST':
                    value = float(value)
                    
                self.tokens.append(Token(kind, value, line_num, column))
                
        self.tokens.append(Token('EOF', '', line_num, len(self.source_code) - line_start + 1))
        return self.tokens

if __name__ == "__main__":
    code = "int a = 10;\nfloat b = 3.14;\nif (a == 10) { b = b + 1.0; }"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    for t in tokens:
        print(t)
    for e in lexer.errors:
        print(e)
