import re

class Optimizer:
    def __init__(self, code):
        self.code = code

    def optimize(self):
        optimized = self.constant_folding_and_propagation(self.code)
        optimized = self.dead_temp_elimination(optimized)
        return optimized

    def _is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def constant_folding_and_propagation(self, code):
        constants = {}
        new_code = []
        
        for instr in code:
            # If label, clear constants to be safe with control flow
            if instr.endswith(':'):
                constants.clear()
                new_code.append(instr)
                continue
                
            # Match assignment: x = y op z
            match_binop = re.match(r'^([\w]+)\s*=\s*([-\w.]+)\s*([+\-*/])\s*([-\w.]+)$', instr)
            if match_binop:
                res_var, left, op, right = match_binop.groups()
                
                # Propagate
                if left in constants: left = constants[left]
                if right in constants: right = constants[right]
                
                # Fold if both are numbers
                if self._is_number(left) and self._is_number(right):
                    try:
                        val = eval(f"{left} {op} {right}")
                        constants[res_var] = str(val)
                        new_code.append(f"{res_var} = {val}")
                        continue
                    except:
                        pass
                
                new_code.append(f"{res_var} = {left} {op} {right}")
                continue

            # Match assignment: x = y
            match_assign = re.match(r'^([\w]+)\s*=\s*([-\w.]+)$', instr)
            if match_assign:
                res_var, right = match_assign.groups()
                
                if right in constants:
                    right = constants[right]
                
                if self._is_number(right):
                    constants[res_var] = right
                    
                new_code.append(f"{res_var} = {right}")
                continue
                
            # Match ifFalse
            match_if = re.match(r'^ifFalse\s+([-\w.]+)\s+goto\s+(L\d+)$', instr)
            if match_if:
                cond, label = match_if.groups()
                if cond in constants:
                    cond = constants[cond]
                new_code.append(f"ifFalse {cond} goto {label}")
                # We do not evaluate conditions to eliminate unreachable branches in this basic optimizer
                continue
                
            # Match print
            match_print = re.match(r'^print\s+([-\w.]+)$', instr)
            if match_print:
                val = match_print.group(1)
                if val in constants:
                    val = constants[val]
                new_code.append(f"print {val}")
                continue
                
            # Other
            new_code.append(instr)
            
        return new_code

    def dead_temp_elimination(self, code):
        # We only eliminate dead temporaries (t1, t2, etc.)
        # that are assigned but never used.
        uses = set()
        
        # Backward pass to find uses
        for instr in reversed(code):
            # Binop: x = y op z -> y, z are used
            match_binop = re.match(r'^[\w]+\s*=\s*([-\w.]+)\s*[+\-*/]\s*([-\w.]+)$', instr)
            if match_binop:
                uses.add(match_binop.group(1))
                uses.add(match_binop.group(2))
            
            # Assign: x = y -> y is used
            match_assign = re.match(r'^[\w]+\s*=\s*([-\w.]+)$', instr)
            if match_assign:
                uses.add(match_assign.group(1))
                
            # ifFalse cond goto L -> cond is used
            match_if = re.match(r'^ifFalse\s+([-\w.]+)\s+goto', instr)
            if match_if:
                uses.add(match_if.group(1))
                
            # return val -> val is used
            match_return = re.match(r'^return\s+([-\w.]+)$', instr)
            if match_return:
                uses.add(match_return.group(1))

            # print val -> val is used
            match_print = re.match(r'^print\s+([-\w.]+)$', instr)
            if match_print:
                uses.add(match_print.group(1))

        # Forward pass to eliminate dead temp assignments
        new_code = []
        for instr in code:
            match_assign = re.match(r'^([\w]+)\s*=', instr)
            if match_assign:
                res_var = match_assign.group(1)
                # If it's a temporary and not in uses, skip it
                if res_var.startswith('t') and res_var not in uses:
                    continue
            new_code.append(instr)
            
        return new_code
