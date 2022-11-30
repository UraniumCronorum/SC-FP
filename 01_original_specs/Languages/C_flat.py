################################
# Author: Wesley Nuzzo

from collections import namedtuple
import _sys

################################
# Exceptions

class VarNotDeclared(Exception):
    pass

class VarNotDefined(Exception):
    pass

################################
# Abstract classes

class SyntaxObject:
    pass

class Expression(SyntaxObject):
    pass

class Instruction(SyntaxObject):
    pass

class Operator(Expression):
    pass

class Terminal(Expression):
    pass

class Type(Terminal):
    pass

################################
# Program

class Program(SyntaxObject):
    
    def __init__(self, variables, *instrs):
        self.variables = variables
        self.instrs = list(instrs)

    def __str__(self):
        v = '(%s)' % ' '.join(var for var in self.variables)
        i = ' '.join(str(instr) for instr in self.instrs)
        return '(program %s %s)' % (v, i)

    def interpret(self):
        env = dict.fromkeys(self.variables)

        self.checkForm()
        for instr in self.instrs[:-1]:
            instr.interpret(env)
        return self.instrs[-1].interpret(env)

    def checkForm(self):
        assert isinstance(self.variables, set)
        for variable in self.variables:
            assert isinstance(variable, str)
        for instr in self.instrs[:-1]:
            assert isinstance(instr, Instruction)
            instr.checkForm()
        assert isinstance(self.instrs[-1], Return)
        self.instrs[-1].checkForm()

class Return(SyntaxObject):

    def __init__(self, out):
        self.out = out

    def __str__(self):
        return '(retn %s)' % self.out

    def interpret(self, env):
        return self.out.interpret(env)

    def checkForm(self):
        assert isinstance(self.out, Expression)
        self.out.checkForm()

####
# I/0
class Read(Expression):

    def __str__(self):
        return '(read)'

    def interpret(self, env):
        return _sys.readInt()

    def checkForm(self):
        return

####
# Types
class Int(Expression):

    def __init__(self, val):
        self.val = val

    def __str__(self):
        return str(self.val)

    def interpret(self, env):
        return self.val

    def checkForm(self):
        assert isinstance(self.val, int)

####
# Operators
class Negative(Operator, namedtuple('Negative', 'expr')):
    
    def __str__(self):
        return '(- %s)' % self
    
    def interpret(self, env):
        expr = self.expr.interpret(env)
        return -expr

    def checkForm(self):
        for subexpr in self:
            assert isinstance(subexpr, Terminal)
            subexpr.checkForm()

class Sum(Operator, namedtuple('Sum', 'lhs rhs')):
    
    def __str__(self):
        return '(+ %s %s)' % self
    
    def interpret(self, env):
        lhs, rhs = (expr.interpret(env) for expr in self)
        return lhs + rhs

    def checkForm(self):
        for subexpr in self:
            assert isinstance(subexpr, Terminal)
            subexpr.checkForm()

####
# Variables and Assignment

class Assign(Instruction, namedtuple('Assign', 'var expr')):
    
    def __str__(self):
        return '(:= %s %s)' % self
    
    def interpret(self, env):
        var = self.var.name
        if var not in env:
            raise VarNotDeclared(self.var)
        env[var] = self.expr.interpret(env)

    def checkForm(self):
        assert isinstance(self.var, Var)
        self.var.checkForm()
        assert isinstance(self.expr, Expression)
        self.expr.checkForm()
        

class Var(Terminal):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def interpret(self, env):
        if self.name not in env:
            raise VarNotDeclared
        if env[self.name] == None:
            raise VarNotDefined(self)
        return env[self.name]

    def checkForm(self):
        assert isinstance(self.name, str)
