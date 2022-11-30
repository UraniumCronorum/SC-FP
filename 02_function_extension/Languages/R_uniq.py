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

    def __init__(self, functions, body):
        self.functions = functions
        self.body = body

    def __str__(self):
        return '(program (%s) %s)' % (' '.join(str(f) for f in self.functions),
                                      self.body)

    def interpret(self):
        self.checkForm()
        env = {}
        for f in self.functions:
            env[f.name] = f
        return self.body.interpret(env)

    def checkForm(self):
        assert isinstance(self.functions, list)
        for f in self.functions:
            assert isinstance(f, Function)
            f.checkForm()
        assert isinstance(self.body, Expression)
        self.body.checkForm()

####
# Functions

class FunctionNotDefined(Exception):
    pass

class WrongNumberOfArgs(Exception):
    pass

class Function(SyntaxObject):
    def __init__(self, name, arguments, body):
        self.name = name
        self.arguments = arguments
        self.body = body

    def __str__(self):
        args_str = ' '.join(str(arg) for arg in self.arguments)
        return '(function %s (%s) %s)' % (self.name, args_str, self.body)

    def interpret(self, *arguments):
        assert len(arguments) == len(self.arguments)
        env = {argname:argval for argname, argval in
               zip(self.arguments,arguments)}
        return self.body.interpret(env)

    def checkForm(self):
        assert isinstance(self.name, Fname)
        assert isinstance(self.arguments, list)
        for arg in self.arguments:
            assert isinstance(arg, Expression)
            arg.checkForm()
        assert isinstance(self.body, Expression)
        self.body.checkForm()

class Fname(SyntaxObject):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return self.name
    def __hash__(self):
        return hash(self.name)
    def __eq__(self, other):
        if isinstance(other, Fname):
            return self.name == other.name
        return False
    def checkForm(self):
        assert isinstance(self.name, str)

class Call(Expression):
    def __init__(self, fname, *args):
        self.fname = fname
        self.args = args

    def __str__(self):
        args_str = ' '.join(str(arg) for arg in self.args)
        return '(%s %s)' % (self.fname, args_str)

    def interpret(self, env):
        if self.fname not in env:
            raise FunctionNotDefined(self.fname)
        if len(env[self.fname].arguments) != len(self.args):
            raise WrongNumberOfArgs(self.fname, len(self.args))
        args = [arg.interpret(env) for arg in self.args]
        return env[self.fname].interpret(*args)

    def checkForm(self):
        assert isinstance(self.fname, Fname)
        self.fname.checkForm()
        for arg in self.args:
            assert isinstance(arg, Expression)
            arg.checkForm()

####
# I/O
class Read(Expression):

    def __str__(self):
        return '(read)'

    def interpret(self, env):
        return _sys.readInt()

    def checkForm(self):
        return

####
# Types
class Int(Type):
    
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
            assert isinstance(subexpr, Expression)
            subexpr.checkForm()

class Sum(Operator, namedtuple('Sum', 'lhs rhs')):

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

    def __str__(self):
        var, expr = self.binding
        bindingStr = '[%s %s]' % (var, expr)
        return '(let (%s) %s)' % (bindingStr, self.body)

    def interpret(self, env):
        newEnv = env.copy()
        assert self.binding not in env
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
            raise VarNotDefined(self.name) from e

    def checkForm(self):
        assert isinstance(self.name, str)

