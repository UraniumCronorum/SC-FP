
from hypothesis import assume
from hypothesis.strategies import *
from Languages import R
import random

####

varnames=characters(whitelist_categories=('Ll',),
                    max_codepoint = 127)

terminals = one_of(builds(R.Int, integers()),
                   builds(R.Var, varnames),
                   just(R.Read()))

####
def extensions(rule):
    return one_of(builds(R.Sum, rule, rule),
                  builds(R.Negative, rule),
                  builds(R.Let, tuples(builds(R.Var, varnames), rule), rule))

expressions = recursive(terminals, extensions)

####
def assignVarNames(expr, defined=set()):
    ''' Change variable names to use defined names.
        Return True if successful, False otherwise. '''
    if isinstance(expr, R.Var):
        if expr.name in defined:
            return True
        elif defined:
            expr.name = random.choice(list(defined))
            return True
        return False
    elif isinstance(expr, R.Let):
        if assignVarNames(expr.binding[1], defined):
            # we know this next step will pass
            assignVarNames(expr.body, defined | {expr.binding[0].name})
            return True
        return False
    elif isinstance(expr, R.Operator):
        out = True
        for i in expr:
            out &= assignVarNames(i, defined)
        return out
    elif type(expr) in (R.Int, R.Read):
        return True
    else:
        raise TypeError(expr)

####

programs = builds(R.Program, expressions)

@composite
def safePrograms(draw):
    out = draw(programs)
    assignVarNames(out.body)
    return out

@composite
def saferPrograms(draw):
    out = draw(programs)
    assume(assignVarNames(out.body))
    return out

if __name__ == '__main__':
    for i in range(8):
        e = saferPrograms().example()
        print(repr(e))
        print(e)

