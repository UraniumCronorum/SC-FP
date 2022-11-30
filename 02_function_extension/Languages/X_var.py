################################
# Author: Wesley Nuzzo
'''
Provides an interpreter for x86, along with some intermediate forms.
'''

from collections import namedtuple

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
        env = {}
        for instr in self.instrs[:-1]:
            instr.interpret(env)
        return self.instrs[-1].interpret(env)

    def checkForm(self):
        for instr in self.instrs:
            assert isinstance(instr, Instruction)
            instr.checkForm()
        assert isinstance(self.instrs[-1], Retq)

class Retq(Instruction):
    RETURN_VAR = 'retvar'

    def __str__(self):
        return 'retq'

    def interpret(self, env):
        return env[self.RETURN_VAR]

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

####
# Memory

class Var(Source, Destination):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return self.name
    def __eq__(self, other):
        if isinstance(other, Var):
            return self.name == other.name
    def __hash__(self):
        return hash(self.name)
    
    def setVal(self, val, env):
        env[self.name] = val
    def getVal(self, env):
        return env[self.name]

    def checkForm(self):
        assert isinstance(self.name, str)
