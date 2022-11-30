################################
# Author: Wesley Nuzzo
'''
Provides an interpreter for x86, along with some intermediate forms.
'''

from collections import namedtuple
from enum import *

########
# Input function
x86_input = '''
input:
    
'''

################################
# Abstract classes #

class SyntaxObject:
    pass

class Source(SyntaxObject):
    pass

class Destination(SyntaxObject):
    pass

class Instruction(SyntaxObject):
    pass

####
# Helper for interpret functions
class Env:
    def __init__(self):
        stackPtr = Addr.SPACE // 2
        self.regs = {Reg.RSP:stackPtr,
                     Reg.RBP:stackPtr}
        self.mem = [None]*Addr.SPACE

####
# Program and Retq
class Program(SyntaxObject):

    def __init__(self, *instrs):
        self.instrs = instrs

    def __str__(self):
        out = '\n.global _main\n_main:\t'
        out += '\n\t'.join(str(instr) for instr in self.instrs)
        return out

    def interpret(self):
        self.checkForm()
        env = Env()
        for instr in self.instrs[:-1]:
            instr.interpret(env)
        return self.instrs[-1].interpret(env)

    def checkForm(self):
        for instr in self.instrs:
            assert isinstance(instr, Instruction)
            instr.checkForm()
        assert isinstance(self.instrs[-1], Retq)

class Retq(Instruction):

    def __str__(self):
        return 'retq'

    def interpret(self, env):
        return Reg.RAX.getVal(env)

    def checkForm(self):
        return

####
# Types
class Int(Source):

    def __init__(self, val):
        self.val = val

    def __str__(self):
        return '$%d' % self.val

    def getVal(self, env):
        return self.val

    def checkForm(self):
        assert isinstance(self.val, int)

####
# Operators

class Movq(Instruction, namedtuple('Movq', 'src dest')):

    def __str__(self):
        return 'movq %s, %s' % self

    def interpret(self, env):
        self.dest.setVal(self.src.getVal(env), env)

    def checkForm(self):
        assert isinstance(self.src, Source)
        self.src.checkForm()
        assert isinstance(self.dest, Destination)
        self.dest.checkForm()
        assert not (isinstance(self.src, Addr) and
                    isinstance(self.dest, Addr))


class Negq(Instruction, namedtuple('Negq', 'dest')):

    def __str__(self):
        return 'negq %s' % self

    def interpret(self, env):
        self.dest.setVal(-self.dest.getVal(env), env)

    def checkForm(self):
        assert isinstance(self.dest, Destination)
        self.dest.checkForm()


class Subq(Instruction, namedtuple('Subq', 'src dest')):

    def __str__(self):
        return 'subq %s, %s' % self

    def interpret(self,env):
        self.dest.setVal(self.dest.getVal(env) - self.src.getVal(env),
                         env)

    def checkForm(self):
        assert isinstance(self.src, Source)
        self.src.checkForm()
        assert isinstance(self.dest, Destination)
        self.dest.checkForm()
        assert not (isinstance(self.src, Addr) and
                    isinstance(self.dest, Addr))

class Addq(Instruction, namedtuple('Addq', 'src dest')):

    def __str__(self):
        return 'addq %s, %s' % self

    def interpret(self, env):
        self.dest.setVal(self.dest.getVal(env) + self.src.getVal(env),
                         env)

    def checkForm(self):
        assert isinstance(self.src, Source)
        self.src.checkForm()
        assert isinstance(self.dest, Destination)
        self.dest.checkForm()
        assert not (isinstance(self.src, Addr) and
                    isinstance(self.dest, Addr))

class Pushq(Instruction, namedtuple('Pushq', 'src')):

    def __str__(self):
        return 'pushq %s' % self

    def interpret(self, env):
        base = Reg.RSP
        base.setVal(base.getVal(env)-1,
                    env)
        Addr(base, 0).setVal(self.src.getVal(env),
                             env)

    def checkForm(self):
        assert isinstance(self.src, Source)
        self.src.checkForm()


class Popq(Instruction, namedtuple('Popq', 'dest')):

    def __str__(self):
        return 'popq %s' % self

    def interpret(self, env):
        base = Reg.RSP
        self.dest.setVal(Addr(base, 0).getVal(env),
                         env)
        assert self.dest.getVal(env) != None
        base.setVal(base.getVal(env)+1,
                    env)

    def checkForm(self):
        assert isinstance(self.dest, Destination)
        self.dest.checkForm()

####
# Memory

class Reg(Source, Destination, Enum):
    RSP = auto()
    RBP = auto()
    RAX = auto()
    RBX = auto()
    RCX = auto()
    RDX = auto()
    RSI = auto()
    RDI = auto()
    R8 = auto()
    R9 = auto()
    R10 = auto()
    R11 = auto()
    R12 = auto()
    R13 = auto()
    R14 = auto()
    R15 = auto()

    def __str__(self):
        return '%%%s' % self.name.lower()

    def getVal(self, env):
        return env.regs[self]

    def setVal(self, val, env):
        env.regs[self] = val

    def checkForm(self):
        return

class Addr(Source, Destination):
    SPACE = 2**8
    WORD_SIZE = 4

    def __init__(self, base, offset):
        self.base = base
        self.offset = offset
        # for interpreter methods
        self._offset = offset // self.WORD_SIZE

    def __str__(self):
        return '%d(%s)' % (self.offset, self.base)

    def __eq__(self, other):
        return self.base == other.base and self.offset == other.offset

    def __hash__(self):
        return hash((self.base, offset))

    def getVal(self, env):
        return env.mem[self.base.getVal(env) + self._offset]

    def setVal(self, val, env):
        env.mem[self.base.getVal(env) + self._offset] = val

    def checkForm(self):
        assert isinstance(self.base, Reg)
        assert isinstance(self.offset, int)
