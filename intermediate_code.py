class TACGenerator:
    def __init__(self, ast):
        self.ast = ast
        self.code = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, instruction):
        self.code.append(instruction)

    def generate(self):
        self._visit(self.ast)
        return self.code

    def _visit(self, node):
        if not node:
            return None

        if node.name == "Program" or node.name == "Block":
            for child in node.children:
                self._visit(child)
            return None
            
        elif node.name == "VarDecl":
            # Just look for an Assign inside VarDecl
            for child in node.children:
                if child.name == "Assign":
                    self._visit(child)
            return None

        elif node.name == "Assign":
            id_val = None
            for child in node.children:
                if child.name.startswith("Id:"):
                    id_val = child.name.split(" ")[1]
                    break
            
            if len(node.children) > 1:
                rhs_result = self._visit(node.children[1])
                if id_val and rhs_result:
                    self.emit(f"{id_val} = {rhs_result}")
            return id_val

        elif node.name.startswith("BinOp:"):
            op = node.name.split(" ")[1]
            left_res = None
            right_res = None
            if len(node.children) > 0:
                left_res = self._visit(node.children[0])
            if len(node.children) > 1:
                right_res = self._visit(node.children[1])
                
            temp = self.new_temp()
            self.emit(f"{temp} = {left_res} {op} {right_res}")
            return temp

        elif node.name.startswith("Int:"):
            return node.name.split(" ")[1]
            
        elif node.name.startswith("Float:"):
            return node.name.split(" ")[1]
            
        elif node.name.startswith("Id:"):
            return node.name.split(" ")[1]
            
        elif node.name == "IfStmt":
            # Children: condition, true_block, optionally false_block
            cond_node = node.children[0]
            true_block = node.children[1]
            false_block = node.children[2] if len(node.children) > 2 else None
            
            cond_res = self._visit(cond_node)
            L_end = self.new_label()
            
            if false_block:
                L_false = self.new_label()
                self.emit(f"ifFalse {cond_res} goto {L_false}")
                self._visit(true_block)
                self.emit(f"goto {L_end}")
                self.emit(f"{L_false}:")
                self._visit(false_block)
                self.emit(f"{L_end}:")
            else:
                self.emit(f"ifFalse {cond_res} goto {L_end}")
                self._visit(true_block)
                self.emit(f"{L_end}:")
            return None

        elif node.name == "WhileStmt":
            # Children: condition, block
            L_start = self.new_label()
            L_end = self.new_label()
            
            self.emit(f"{L_start}:")
            cond_res = self._visit(node.children[0])
            self.emit(f"ifFalse {cond_res} goto {L_end}")
            
            self._visit(node.children[1])
            self.emit(f"goto {L_start}")
            self.emit(f"{L_end}:")
            return None

        elif node.name == "ReturnStmt":
            if len(node.children) > 0:
                ret_val = self._visit(node.children[0])
                self.emit(f"return {ret_val}")
            else:
                self.emit("return")
            return None
            
        elif node.name == "PrintStmt":
            if len(node.children) > 0:
                print_val = self._visit(node.children[0])
                self.emit(f"print {print_val}")
            return None
            
        elif node.name == "Else":
            for child in node.children:
                self._visit(child)
            return None

        return None
