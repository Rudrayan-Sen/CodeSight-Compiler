class ASTNode:
    def __init__(self, name):
        self.name = name
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def __repr__(self, level=0):
        ret = "\t" * level + repr(self.name) + "\n"
        for child in self.children:
            if isinstance(child, ASTNode):
                ret += child.__repr__(level + 1)
            else:
                ret += "\t" * (level + 1) + repr(child) + "\n"
        return ret

class Parser:
    def __init__(self, tokens):
        # Filter out ERROR tokens for parsing, we only parse conceptually valid streams
        # or we just stop. We'll include them and handle them.
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos] if self.tokens else None
        self.errors = []

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

    def match(self, expected_type, expected_value=None):
        if self.current_token and self.current_token.type == expected_type:
            if expected_value is None or self.current_token.value == expected_value:
                token = self.current_token
                self.advance()
                return token
        
        err_msg = f"Syntax Error at line {self.current_token.line if self.current_token else 'EOF'}: Expected {expected_type} {expected_value if expected_value else ''}, got {self.current_token.type if self.current_token else 'EOF'} '{self.current_token.value if self.current_token else ''}'"
        self.errors.append(err_msg)
        
        # Panic mode recovery: advance until we find a semicolon or EOF
        self.advance()
        while self.current_token and self.current_token.type != 'EOF' and not (self.current_token.type == 'DELIMITER' and self.current_token.value == ';'):
            self.advance()
        if self.current_token and self.current_token.value == ';':
            self.advance() # consume ';'
        return None

    def parse(self):
        root = ASTNode("Program")
        while self.current_token and self.current_token.type != 'EOF':
            if self.current_token.type == 'ERROR':
                self.advance() # Skip lexical errors
                continue
            stmt = self.parse_statement()
            if stmt:
                root.add_child(stmt)
        return root, self.errors

    def parse_statement(self):
        if self.current_token.type == 'KEYWORD':
            if self.current_token.value in ['int', 'float']:
                return self.parse_var_decl()
            elif self.current_token.value == 'if':
                return self.parse_if_stmt()
            elif self.current_token.value == 'while':
                return self.parse_while_stmt()
            elif self.current_token.value == 'return':
                return self.parse_return_stmt()
            elif self.current_token.value == 'print':
                return self.parse_print_stmt()
        elif self.current_token.type == 'IDENTIFIER':
            return self.parse_assignment()
            
        # If we reach here, it's either an error or empty statement
        if self.current_token.type == 'DELIMITER' and self.current_token.value == ';':
            self.advance() # Empty statement
            return None
            
        self.errors.append(f"Syntax Error at line {self.current_token.line}: Unexpected token '{self.current_token.value}'")
        self.advance() # Panic recovery
        return None

    def parse_var_decl(self):
        node = ASTNode("VarDecl")
        type_token = self.match('KEYWORD') # int or float
        if type_token:
            node.add_child(ASTNode(f"Type: {type_token.value}"))
            
        id_token = self.match('IDENTIFIER')
        if id_token:
            node.add_child(ASTNode(f"Id: {id_token.value}"))
            
        if self.current_token and self.current_token.type == 'OPERATOR' and self.current_token.value == '=':
            self.advance() # match '='
            expr_node = self.parse_expression()
            if expr_node:
                assign_node = ASTNode("Assign")
                assign_node.add_child(ASTNode(f"Id: {id_token.value}"))
                assign_node.add_child(expr_node)
                node.add_child(assign_node)
                
        self.match('DELIMITER', ';')
        return node

    def parse_assignment(self):
        node = ASTNode("Assign")
        id_token = self.match('IDENTIFIER')
        if id_token:
            node.add_child(ASTNode(f"Id: {id_token.value}"))
            
        if self.match('OPERATOR', '='):
            expr_node = self.parse_expression()
            if expr_node:
                node.add_child(expr_node)
                
        self.match('DELIMITER', ';')
        return node

    def parse_if_stmt(self):
        node = ASTNode("IfStmt")
        self.match('KEYWORD', 'if')
        self.match('DELIMITER', '(')
        
        condition = self.parse_expression()
        if condition:
            node.add_child(condition)
            
        self.match('DELIMITER', ')')
        
        true_block = self.parse_block()
        if true_block:
            node.add_child(true_block)
            
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value == 'else':
            self.advance()
            else_node = ASTNode("Else")
            false_block = self.parse_block()
            if false_block:
                else_node.add_child(false_block)
            node.add_child(else_node)
            
        return node

    def parse_while_stmt(self):
        node = ASTNode("WhileStmt")
        self.match('KEYWORD', 'while')
        self.match('DELIMITER', '(')
        
        condition = self.parse_expression()
        if condition:
            node.add_child(condition)
            
        self.match('DELIMITER', ')')
        
        block = self.parse_block()
        if block:
            node.add_child(block)
            
        return node

    def parse_return_stmt(self):
        node = ASTNode("ReturnStmt")
        self.match('KEYWORD', 'return')
        expr = self.parse_expression()
        if expr:
            node.add_child(expr)
        self.match('DELIMITER', ';')
        return node

    def parse_print_stmt(self):
        node = ASTNode("PrintStmt")
        self.match('KEYWORD', 'print')
        self.match('DELIMITER', '(')
        expr = self.parse_expression()
        if expr:
            node.add_child(expr)
        self.match('DELIMITER', ')')
        self.match('DELIMITER', ';')
        return node

    def parse_block(self):
        block_node = ASTNode("Block")
        if self.current_token and self.current_token.type == 'DELIMITER' and self.current_token.value == '{':
            self.advance()
            while self.current_token and not (self.current_token.type == 'DELIMITER' and self.current_token.value == '}'):
                if self.current_token.type == 'EOF':
                    self.errors.append("Syntax Error: Unexpected EOF, expected '}'")
                    break
                stmt = self.parse_statement()
                if stmt:
                    block_node.add_child(stmt)
            self.match('DELIMITER', '}')
        else:
            # Single statement block
            stmt = self.parse_statement()
            if stmt:
                block_node.add_child(stmt)
        return block_node

    def parse_expression(self):
        # Handles relational as top level
        node = self.parse_additive()
        if self.current_token and self.current_token.type == 'OPERATOR' and self.current_token.value in ['==', '!=', '<', '>', '<=', '>=']:
            op_token = self.current_token
            self.advance()
            right = self.parse_additive()
            new_node = ASTNode("BinOp: " + op_token.value)
            if node: new_node.add_child(node)
            if right: new_node.add_child(right)
            return new_node
        return node

    def parse_additive(self):
        node = self.parse_multiplicative()
        while self.current_token and self.current_token.type == 'OPERATOR' and self.current_token.value in ['+', '-']:
            op_token = self.current_token
            self.advance()
            right = self.parse_multiplicative()
            new_node = ASTNode("BinOp: " + op_token.value)
            if node: new_node.add_child(node)
            if right: new_node.add_child(right)
            node = new_node
        return node

    def parse_multiplicative(self):
        node = self.parse_factor()
        while self.current_token and self.current_token.type == 'OPERATOR' and self.current_token.value in ['*', '/']:
            op_token = self.current_token
            self.advance()
            right = self.parse_factor()
            new_node = ASTNode("BinOp: " + op_token.value)
            if node: new_node.add_child(node)
            if right: new_node.add_child(right)
            node = new_node
        return node

    def parse_factor(self):
        token = self.current_token
        if not token:
            return None
            
        if token.type == 'INT_CONST':
            self.advance()
            return ASTNode(f"Int: {token.value}")
        elif token.type == 'FLOAT_CONST':
            self.advance()
            return ASTNode(f"Float: {token.value}")
        elif token.type == 'IDENTIFIER':
            self.advance()
            return ASTNode(f"Id: {token.value}")
        elif token.type == 'DELIMITER' and token.value == '(':
            self.advance()
            node = self.parse_expression()
            self.match('DELIMITER', ')')
            return node
            
        self.errors.append(f"Syntax Error at line {token.line}: Unexpected token '{token.value}' in expression")
        self.advance() # Panic recovery
        return None
