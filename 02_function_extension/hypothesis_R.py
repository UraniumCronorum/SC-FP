
from Languages import R

from hypothesis.strategies import *
from hypothesis import assume
import random

####
# Simple Expressions
varnames=characters(whitelist_categories=('Ll',),
                    max_codepoint = 127)

terminals = one_of(builds(R.Int, integers()),
                   builds(R.Var, characters(whitelist_categories=('Ll',),
                                          max_codepoint = 127)),
                   just(R.Read()))

def extensions(rule):
    return one_of(builds(R.Sum, rule, rule),
                  builds(R.Negative, rule),
                  builds(R.Let, tuples(builds(R.Var, varnames), rule), rule))

expressions = recursive(terminals, extensions)

####
# Functions

function_headers = builds(R.Function,
                          builds(R.Fname, varnames),
                          lists(builds(R.Var, varnames)),
                          none())

##def functions_from_header(header, funcdefs):
##    # modifies header in place
##    body = body_exprs_from_spec(funcdefs)
##    header.body = body_exprs_from_spec(funcdefs)
##    return header

def spec_from_headers(headers):
    out = {}
    for header in headers:
        fname = header.name
        n_vars = len(header.arguments)
        out [fname] = n_vars
    # note that only most recent definition of function applies
    return out

@composite
def funccalls(draw, funcdefs):
    # sorted_defs = sorted(funcdefs, key=lambda k: (len(k.arguments), k.name))
    f = draw(sampled_from(list(funcdefs)) if funcdefs else nothing())
    n_args = funcdefs[f]
    args = draw(lists(expressions, min_size=n_args, max_size=n_args))
    return R.Call(f, *args)

def body_exprs_from_spec(funcdefs):
    def body_extensions(rule):
        return (builds(R.Sum, expressions, expressions) |
                builds(R.Negative, expressions) |
                builds(R.Let,
                       tuples(builds(R.Var, varnames), expressions),
                       rule) |
                funccalls(funcdefs))
    return recursive(terminals, body_extensions)

# e.g. body_exprs_from_spec({'foo':3})

####
# Reassign Variable names and Function calls

def assignVarNames(expr, vars_=set(), fcns=set()):
    ''' Change variable names to use defined names.
        Return True if successful, False otherwise.

        Note that we "short-circuit": if a subexpression fails to pass,
        we may skip the rest of the expression.'''
    if isinstance(expr, R.Var):
        if expr.name in vars_:
            return True
        elif vars_:
            expr.name = random.choice(list(vars_))
            return True
        return False
    elif isinstance(expr, R.Let):
        if assignVarNames(expr.binding[1], vars_, fcns):
            # we know this next step will pass
            assignVarNames(expr.body, vars_ | {expr.binding[0].name}, fcns)
            return True
        return False
    elif isinstance(expr, R.Operator):
        out = True
        for i in expr:
            out &= assignVarNames(i, vars_, fcns)
        return out
    elif isinstance(expr, R.Call):
        # note that all() "short-ciruits" on False
        # using lists rather than generators to avoid that
        if expr.fname in fcns:
            return all(assignVarNames(arg, vars_, fcns)
                       for arg in expr.args)
        elif fcns:
            expr.name = random.choice(list(fcns))
            return all(assignVarNames(arg, vars_, fcns)
                       for arg in expr.args)
        return False
    elif type(expr) in (R.Int, R.Read):
        return True
    else:
        raise TypeError(expr)

####
# Programs

simple_programs = builds(R.Program, just([]), expressions)

@composite
def full_programs(draw):
    headers = draw(lists(function_headers))    
    spec = spec_from_headers(headers)
    for function in headers:
        function.body = draw(body_exprs_from_spec(spec))
    body = draw(body_exprs_from_spec(spec))
    return R.Program(headers, body)


####

programs = full_programs()

@composite
def safePrograms(draw):
    out = draw(programs)
    fspecs = {i.name:{j.name for j in i.arguments} for i in out.functions}
    fnames = set(fspecs.keys())
    for i in out.functions:
        v = fspecs[i.name]
        assignVarNames(i.body, vars_=v, fcns=fnames)
    assignVarNames(out.body, vars_=set(), fcns=fnames)
    return out


###
# best way to speed this up may be to force every function to have an argument
# and maybe require at least two functions to be defined

function_headers_s = builds(R.Function,
                            builds(R.Fname, varnames),
                            lists(builds(R.Var, varnames), min_size=1),
                            none())
@composite
def full_programs_safer(draw):
    headers = draw(lists(function_headers_s))
    spec = spec_from_headers(headers)
    for function in headers:
        function.body = draw(body_exprs_from_spec(spec))
    body = draw(body_exprs_from_spec(spec))
    return R.Program(headers, body)

@composite
def saferPrograms(draw):
    out = draw(full_programs_safer())
    fspecs = {i.name:{j.name for j in i.arguments} for i in out.functions}
    fnames = set(fspecs.keys())
    for i in out.functions:
        v = fspecs[i.name]
        assert (assignVarNames(i.body, vars_=v, fcns=fnames))
    assume(assignVarNames(out.body, vars_=set(), fcns=fnames))
    return out

####
# main
if __name__ == '__main__':
    for i in range(32):
        p = saferPrograms().example()
        print(p)
##    for i in range(8):
##        l = lists(function_headers_s,min_size=3, max_size=8).example()
##        print([str(i) for i in l])
##    for i in range(8):
##        e = body_exprs_from_spec({}).example()
##        e.checkForm()
##        print(e)
