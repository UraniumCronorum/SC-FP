################################
# Author: Wesley Nuzzo

from collections import namedtuple
import _sys

################################
# Exceptions #

class VarNotDefined(Exception):
    pass

################################
# Abstract classes #

class SyntaxObject:
    pass

class Expression(SyntaxObject):
    pass

class Type(Expression):
    pass

class Operator(Expression):
    pass

################################
# Program #

class Program(SyntaxObject):

    def __init__(self, body):
        self.body = body

    def __repr__(self):
        return 'R.Program(%s)' % repr(self.body)

    def __str__(self):
        return '(program %s)' % str(self.body)

    def interpret(self):
        env = {}
        self.checkForm()
        return self.body.interpret(env)

    def checkForm(self):
        assert isinstance(self.body, Expression)
        self.body.checkForm()

####
# I/O
class Read(Expression):

    def __str__(self):
        return '(read)'

    def __repr__(self):
        return 'R.Read()'

    def interpret(self, env):
        return _sys.readInt()

    def checkForm(self):
        return

####
# Types
class Int(Type):
    
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return 'R.Int(%d)' % self.val

    def __str__(self):
        return str(self.val)

    def interpret(self, env):
        return self.val

    def checkForm(self):
        assert isinstance(self.val, int)

####
# Operators
class Negative(Operator, namedtuple('Negative', 'expr')):

    def __repr__(self):
        return 'R.Negative(%r)' % self

    def __str__(self):
        return '(- %s)' % self

    def interpret(self, env):
        expr = self.expr.interpret(env)
        return -expr

    def checkForm(self):
        for subexpr in self:
            assert isinstance(subexpr, Expression)
            subexpr.checkForm()

class Sum(Operator, namedtuple('Sum', 'lhs rhs')):

    def __repr__(self):
        return 'R.Sum(%r, %r)' % self

    def __str__(self):
        return '(+ %s %s)' % self

    def interpret(self, env):
        lhs, rhs = (expr.interpret(env) for expr in self)
        return lhs + rhs

    def checkForm(self):
        for subexpr in self:
            assert isinstance(subexpr, Expression)
            subexpr.checkForm()

####
# Variables and Frames

class Let(Expression):

    def __init__(self, binding, body):
        self.body = body
        self.binding = binding

    def __repr__(self):
        return 'R.Let(%r, %r)' % (self.binding, self.body)

    def __str__(self):
        var, expr = self.binding
        bindingStr = '[%s %s]' % (var, expr)
        return '(let (%s) %s)' % (bindingStr, self.body)

    def interpret(self, env):
        newEnv = env.copy()
        newEnv[self.binding[0]] = self.binding[1].interpret(env)
        return self.body.interpret(newEnv)

    def checkForm(self):
        assert isinstance(self.binding, tuple)
        assert isinstance(self.binding[0], Var)
        assert isinstance(self.binding[1], Expression)
        for i in self.binding:
            i.checkForm()
        assert isinstance(self.body, Expression)
        self.body.checkForm()

class Var(Expression):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'R.Var(%r)' % self.name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def interpret(self, env):
        try:
            return env[self]
        except KeyError as e:
            raise VarNotDefined(self.name) from None

    def checkForm(self):
        assert isinstance(self.name, str)

