
from enum import Enum

from Languages import X_var, X_approx

def gen_homes():
    ''' Generator for new variable homes. Starts with registers, then uses stack.'''
    for i in range(4, 17):
        yield X_approx.Reg(i)
    i = 0
    while True:
        yield x86.Addr(X_approx.Reg.RBP, offset = i)
        i -= 4

########
# Simplest approach
########

def get_vars(instrs):
    out = set()
    for instr in instrs:
        ty = type(instr)
        
        # Dest
        if ty in (X_var.Movq, X_var.Addq, X_var.Subq, X_var.Negq):
            out |= {instr.dest}
        # Src
        if ty in (X_var.Movq, X_var.Addq, X_var.Subq):
            if isinstance(instr.src, X_var.Var):
                out |= {instr.src}
    return out

def simpleAlloc(variables):
    ''' Put everything on the stack'''
    assert X_var.Var('retvar') in variables
    out = {X_var.Var('retvar'):X_approx.Reg.RAX}
    variables -= {X_var.Var('retvar')}
    
    for i, v in enumerate(variables):
        out[v] = X_approx.Addr(X_approx.Reg.RBP, -4*i)
    return out

########
### Saturation Algorithm
########

class Graph:
    def __init__(self, nodes=set()):
        self.data = dict.fromkeys(nodes, set())

    def __str__(self):
        return str(self.data)

    def check_nodes(self, *nodes):
        for node in nodes:
            if node not in self.data.keys():
                self.data[node] = set()

    def add_edge(self, start, end, directed = False):
        self.check_nodes(start, end)
        self.data[start] |= {end}
        if not directed:
            self.data[end] |= {start}

    def remove_edge(self, start, end, directed = False):
        self.data[start] -= {end}
        if not directed:
            self.data[end] -= {start}

    def get_adjacent(self, node):
        if node in self.data:
            return self.data[node]
        return set()

def annotate_liveness(instrs):
    ''' Return a list of tuples containing the instructions along with the set of variables
    live after the instruction.'''
    out = []
    live = set()
    for instr in reversed(instrs):
        # add instruction along with liveness annotation to output
        out.insert(0, (instr, live.copy()))

        # compute liveness for previous instruction
        ty = type(instr)

        # Retq
        if ty == X_var.Retq:
            # retvar must be live
            live |= {X_var.Var('retvar')}
        
        # Dest
        if ty in (X_var.Movq,):
            # These instructions overwrite dest, so dest cannot be live before them
            if type(instr.dest) == X_var.Var:
                live -= {instr.dest}
        elif ty in (X_var.Negq, X_var.Addq, X_var.Subq):
            # These instructions use dest as input, so dest must be live before them
            if type(instr.dest) == X_var.Var:
                live |= {instr.dest}

        # Src
        if ty in (X_var.Movq, X_var.Addq, X_var.Subq):
            # Src must be live
            if type(instr.src) == X_var.Var:
                live |= {instr.src}
    return out

def calc_interference(instrs):
    ''' Given a list of instructions annotated with their liveness, compute the interference graph.'''

    out = Graph()
    for instr in instrs:
        instruction, live_after = instr
        ty = type(instr[0])
        # Mov is a special case, because it doesn't change the value at all
        if ty == X_var.Movq:
            for var in live_after:
                if var not in instruction:
                    out.add_edge(instruction.dest, var)
        # normal cases
        elif ty in (X_var.Negq, X_var.Addq, X_var.Subq):
            for var in live_after:
                if var != instruction.dest:
                    out.add_edge(instruction.dest, var)
    return out

def saturationAlloc(variables, interference):
    ''' Allocate using graph coloring via the saturation method.

    interference: a dictionary representing the interference graph
    '''
    saturation = {var:set() for var in variables}
    out = {}

    # Start by allocating retvar
    rvar = X_var.Var('retvar') 
    assert rvar in variables
    out[rvar] = X_approx.Reg.RAX
    for var in interference.get_adjacent(rvar):
        saturation[var] |= {X_approx.Reg.RAX}
    variables -= {rvar}

    stackIndex=0
    for var in variables:
        # Allocate a register if possible
        for i in range(3, 16):
            reg = X_approx.Reg(i)
            if reg not in saturation[var]:
                out[var] = reg
                for v in interference.get_adjacent(var):
                    saturation[v] |= {reg}
                break
        # Use stack if necessary
        if var not in out.keys():
            out[var] = X_approx.Addr(X_approx.Reg.RBP, stackIndex)
            stackIndex -= X_approx.Addr.WORD_SIZE
    return out, stackIndex // -X_approx.Addr.WORD_SIZE

