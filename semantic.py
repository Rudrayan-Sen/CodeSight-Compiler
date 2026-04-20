class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def declare(self, name, type_):
        if name in self.symbols:
            return False
        self.symbols[name] = {'type': type_, 'initialized': False}
        return True

    def lookup(self, name):
        return self.symbols[name]['type'] if name in self.symbols else None

    def get_all(self):
        return {name: val['type'] for name, val in self.symbols.items()}

    def is_initialized(self, name):
        return self.symbols[name]['initialized'] if name in self.symbols else False

    def set_initialized(self, name):
        if name in self.symbols:
            self.symbols[name]['initialized'] = True

class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.symbol_table = SymbolTable()
        self.errors = []

    def analyze(self):
        self._visit(self.ast)
        return self.symbol_table, self.errors

    def _visit(self, node):
        if not node:
            return None

        if node.name == "Program" or node.name == "Block":
            for child in node.children:
                self._visit(child)
        
        elif node.name == "VarDecl":
            # first child is Type, second is Id, optional third is Assign
            type_val = None
            id_val = None
            assign_node = None
            for child in node.children:
                if child.name.startswith("Type:"):
                    type_val = child.name.split(" ")[1]
                elif child.name.startswith("Id:"):
                    id_val = child.name.split(" ")[1]
                elif child.name == "Assign":
                    assign_node = child
            
            if id_val and type_val:
                if not self.symbol_table.declare(id_val, type_val):
                    self.errors.append(f"Semantic Error: Duplicate declaration of variable '{id_val}'")
                    
            if assign_node:
                self._visit(assign_node)

        elif node.name == "Assign":
            id_val = None
            for child in node.children:
                if child.name.startswith("Id:"):
                    id_val = child.name.split(" ")[1]
                    break
            
            if id_val:
                if not self.symbol_table.lookup(id_val):
                    self.errors.append(f"Semantic Error: Undeclared variable '{id_val}'")
            
            # evaluate RHS BEFORE marking as initialized
            if len(node.children) > 1:
                self._visit(node.children[1])
                
            # now mark it as initialized since it has been assigned
            if id_val and self.symbol_table.lookup(id_val):
                self.symbol_table.set_initialized(id_val)
                
        elif node.name.startswith("BinOp:"):
            # visit left and right
            left_type = None
            right_type = None
            if len(node.children) > 0:
                self._visit(node.children[0])
            if len(node.children) > 1:
                self._visit(node.children[1])
                
        elif node.name == "IfStmt" or node.name == "WhileStmt":
            # first child is condition, followed by block, optional else
            for child in node.children:
                self._visit(child)
                
        elif node.name == "ReturnStmt":
            for child in node.children:
                self._visit(child)

        elif node.name == "PrintStmt":
            for child in node.children:
                self._visit(child)

        elif node.name.startswith("Id:"):
            id_val = node.name.split(" ")[1]
            if not self.symbol_table.lookup(id_val):
                self.errors.append(f"Semantic Error: Undeclared variable '{id_val}'")
            elif not self.symbol_table.is_initialized(id_val):
                self.errors.append(f"Semantic Error: Uninitialized variable '{id_val}' used in expression")
                
        elif node.name == "Else":
            for child in node.children:
                self._visit(child)
