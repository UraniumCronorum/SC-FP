
from Languages import R, R_uniq, C_flat, X_var, X_approx, X
from functools import reduce

########
# Uniquify

def uniquify(expr, used_v = {}, used_f = {}):
    ''' Naming convention: variable name followed by number of used var names.'''
    ty = type(expr)
    if ty == R.Program:
        fcns = []
        for f in expr.functions:
            name = f.name.name
            used_f[name] = used_f.get(name, 0) + 1
            name = name + '-f' + str(used_f[name])
            fcns.append(R_uniq.Function(R_uniq.Fname(name),
                                        f.arguments,
                                        f.body))
        for f in fcns:
            args = []
            local_v = used_v.copy()
            for arg in f.arguments:
                local_v[arg.name] = local_v.get(arg.name, 0) + 1
                name = arg.name + '-v' + str(local_v[arg.name])
                args.append(R_uniq.Var(name))
            f.arguments = args
            f.body = uniquify(f.body, local_v, used_f)
        return R_uniq.Program(fcns, uniquify(expr.body, used_v, used_f))
    # I/0
    elif ty == R.Read:
        return R_uniq.Read()
    # Type
    elif ty == R.Int:
        return R_uniq.Int(expr.val)
    # Operators
    elif ty == R.Negative:
        return R_uniq.Negative(uniquify(expr.expr, used_v, used_f))
    elif ty == R.Sum:
        return R_uniq.Sum(uniquify(expr.lhs, used_v, used_f),
                          uniquify(expr.rhs, used_v, used_f))
    # Variables
    elif ty == R.Var:
        try:
            name = expr.name + '-v' + str(used_v[expr.name])
            return R_uniq.Var(name)
        except KeyError as e:
            raise R.VarNotDefined from e
    elif ty == R.Let:
        new = used_v.copy()
        var, subexpr = expr.binding
        name = var.name
        if name in used_v:
            new[name] += 1
        else:
            new[name] = 0
        new_binding = (R_uniq.Var(name + '-v' + str(new[name])),
                       uniquify(subexpr, used_v, used_f))
        return R_uniq.Let(new_binding,
                          uniquify(expr.body, new, used_f))
    elif ty == R.Call:
        args = [uniquify(arg, used_v, used_f) for arg in expr.args]
        try:
            name = expr.fname.name + '-f' + str(used_f[expr.fname.name])
            name = R_uniq.Fname(name)
            return R_uniq.Call(name, *args)
        except KeyError as e:
            raise R.FunctionNotDefined from e
    else:
        raise TypeError('uniquify: %s' % str(expr))


########
# Flatten

def circleFlatten(expr, ans=None):
    ty = type(expr)
    # idea: functions are translated exactly as normal, just with args
    # program translates functions and then creates a main function
    # also need to add the call operation
    if ty == R_uniq.Program:
        fcns, body = expr.functions, expr.body
        compiled_functions = [circleFlatten(function) for function in fcns]
        main_function = circleFlatten(R_uniq.Function('main', [], body))
        return C_flat.Program(main_function, *compiled_functions)
    elif ty == R_uniq.Function:
        assert ans == None
        ans = 'retvar'
        body = circleFlatten(expr.body, ans)
        return C_flat.Function(expr.name, expr.arguments,
                               {ans}|body.variables,
                               *body.instrs + [C_flat.Return(C_flat.Var(ans))])
    # I/0
    elif ty == R_uniq.Read:
        return C_flat.Function(None, set(), {ans},
                               C_flat.Assign(C_flat.Var(ans), C_flat.Read()))
    # Type
    elif ty == R_uniq.Int:
        return C_flat.Function(None, set(), {ans},
                              C_flat.Assign(C_flat.Var(ans), C_flat.Int(expr.val)))
    elif ty == R_uniq.Negative:
        subexpr = circleFlatten(expr.expr, ans)
        return C_flat.Function(None, set(),
                               subexpr.variables,
                               *subexpr.instrs +
                               [C_flat.Assign(C_flat.Var(ans),
                                              C_flat.Negative(C_flat.Var(ans)))])
    elif ty == R_uniq.Sum:
        helper = ans + '-sum-rhs'
        lhs, rhs = (circleFlatten(expr.lhs, ans),
                    circleFlatten(expr.rhs, helper))
        return C_flat.Function(None, set(),
                               lhs.variables|rhs.variables,
                               *lhs.instrs+rhs.instrs+
                               [C_flat.Assign(C_flat.Var(ans),
                                              C_flat.Sum(C_flat.Var(ans),
                                                         C_flat.Var(helper)))])
    elif ty == R_uniq.Var:
        return C_flat.Function(None, set(),
                               {ans, expr.name},
                               C_flat.Assign(C_flat.Var(ans),
                                             C_flat.Var(expr.name)))
    elif ty == R_uniq.Let:
        var, subexpr = expr.binding
        bindingExpr = circleFlatten(subexpr, var.name)
        bodyExpr = circleFlatten(expr.body, ans)
        return C_flat.Function(None, set(),
                               bindingExpr.variables|bodyExpr.variables,
                               *bindingExpr.instrs + bodyExpr.instrs)
    elif ty == R_uniq.Call:
        name, args = expr.name, expr.args
        arg_stmts = [circleFlatten(arg, name + '-arg-' + str(i))
                     for i, arg in enumerate(args)]
        return C_flat.Function(None, set(),
                               reduce(lambda a,b:a|b,
                                      [arg.variables for arg in arg_stmts],
                                      set()),
                               *(reduce(lambda a,b:a+b, (arg.instrs for arg in arg_stmts), []) +
                                 C_flat.Call(name, *[name + '-arg-' + str(i)
                                                     for i, _ in enumerate(args)])))
    else:
        raise Exception('circleFlatten: %s' % str(expr))

def squareFlatten(expr):
    raise TypeError('circleFlatten: %s' % str(expr))


########
# Select Instruction

def select_instr(program):
    instrs = []
    for instr in program.instrs:
        if type(instr) == C_flat.Assign:
            dest, src = instr
            ty = type(src)
            if ty == C_flat.Int:
                instrs.append(X_var.Movq(X_var.Int(src.val),
                                         X_var.Var(dest.name)))
            elif ty == C_flat.Negative:
                assert type(src.expr) == C_flat.Var
                instrs.append(X_var.Movq(X_var.Var(src.expr.name),
                                         X_var.Var(dest.name)))
                instrs.append(X_var.Negq(X_var.Var(dest.name)))
            elif ty == C_flat.Sum:
                assert type(src.lhs) == C_flat.Var
                assert type(src.rhs) == C_flat.Var
                if src.lhs.name == dest.name:
                    instrs.append(X_var.Movq(X_var.Var(src.lhs.name),
                                             X_var.Var(dest.name)))
                    instrs.append(X_var.Addq(X_var.Var(src.rhs.name),
                                             X_var.Var(dest.name)))
                else:
                    instrs.append(X_var.Movq(X_var.Var(src.rhs.name),
                                             X_var.Var(dest.name)))
                    instrs.append(X_var.Addq(X_var.Var(src.lhs.name),
                                             X_var.Var(dest.name)))
            elif ty == C_flat.Var:
                instrs.append(X_var.Movq(X_var.Var(src.name),
                                         X_var.Var(dest.name)))
            else:
                raise TypeError('select_instr (assign): %s' % str(src))
        elif type(instr) == C_flat.Return:
            assert type(instr.out) == C_flat.Var

            given = instr.out.name
            wanted = X_var.Retq.RETURN_VAR
            if given != wanted:
                instrs.append(X_var.Movq(X_var.Var(given),
                                         X_var.Var(wanted)))
            instrs.append(X_var.Retq())
        else:
            raise TypeError('select_instr: %s' % str(instr))
    return X_var.Program(*instrs)


########
# Assign homes

from r_alloc import *

ah_dict = {
    X_var.Movq: X_approx.Movq,
    X_var.Negq: X_approx.Negq,
    X_var.Addq: X_approx.Addq,
    X_var.Subq: X_approx.Subq
    }
def assign_homes(program):
    ## Register allocation / other analysis

    # count variables in program
    _vars = get_vars(program.instrs)

    # analyze in preparation for register allocation
    annotated_instrs = annotate_liveness(program.instrs)
    interference = calc_interference(annotated_instrs)

    # allocate
    homes, k = saturationAlloc(_vars, interference)
    #homes, k = simpleAlloc(_vars), len(_vars)
    k = k+1 if k%2 else k

    ## Output

    instrs =[X_approx.Pushq(X_approx.Reg.RBP),
             X_approx.Movq(X_approx.Reg.RSP,
                           X_approx.Reg.RBP),
             X_approx.Subq(X_approx.Int(k),
                           X_approx.Reg.RSP)]
    assert isinstance(program.instrs[-1], X_var.Retq)
    for line in program.instrs[:-1]:
        args = []
        for arg in line:
            if type(arg) == X_var.Var:
                args.append(homes[arg])
            elif type(arg) == X_var.Int:
                args.append(X_approx.Int(arg.val))
            else:
                raise TypeError('assignHomes: %s' % str(instr))
        ty = type(line)
        instrs.append(ah_dict[ty](*args))
    instrs += [X_approx.Addq(X_approx.Int(k),
                             X_approx.Reg.RSP),
               X_approx.Popq(X_approx.Reg.RBP),
               X_approx.Retq()]
    return X_approx.Program(*instrs)
    return program

########
# Patch

patch_dict = {
    X_approx.Movq: X.Movq,
    X_approx.Negq: X.Negq,
    X_approx.Addq: X.Addq,
    X_approx.Subq: X.Subq,
    X_approx.Pushq: X.Pushq,
    X_approx.Popq: X.Popq,
    }
def patch(program):
    instrs = []
    for instr in program.instrs[:-1]:
        newTy = patch_dict[type(instr)]
        args = []
        for arg in instr:
            if type(arg) == X_approx.Int:
                args.append(X.Int(arg.val))
            elif type(arg) == X_approx.Reg:
                args.append(X.Reg(arg.value))
            elif type(arg) == X_approx.Addr:
                args.append(X.Addr(X.Reg(arg.base.value),
                                   arg.offset))
            else:
                raise TypeError('patch: %s', instr)
        if len(args) == 2 and (isinstance(args[0], X.Addr) and
                               isinstance(args[1], X.Addr)):
            instrs.append(X.Movq(args[0],
                                 X.Reg.R15))
            instrs.append(newTy(X.Reg.R15,
                                args[1]))
        else:
            instrs.append(newTy(*args))
    instrs.append(X.Retq())
    return X.Program(*instrs)

########
# Pipeline

def readIn(path):
    with open(path, 'r') as fi:
        data = fi.read()
    namespace = locals().copy()
    exec(data, namespace)
    out = namespace['program']
    out.checkForm()
    return out

def pipeline(program):
    steps = (uniquify, circleFlatten, select_instr, assign_homes, patch)
    out = [program]
    for step in steps:
        program = step(program)
        out.append(program)
    return out

def partial_pipeline(program):
    steps = (uniquify, circleFlatten, select_instr, assign_homes, patch)
    out = [program]
    for step in steps:
        try:
            program = step(program)
            out.append(program)
        except Exception as e:
            return out, e
    return out, None

def writeOut(program, path):
    out = str(program)
    with open(path, 'w') as fi:
        fi.write(out)


def log(results, infile, outfile):
    with open('compilation.log', 'a') as fi:
        fi.write('='*32+'\n')
        fi.write(infile + ' -> ' + outfile + '\n')
        fi.write('='*32+'\n')
        for result in results:
            fi.write(str(result))
            fi.write('\n')
            fi.write(str(result.interpret()))
            fi.write('\n')
            fi.write('\n')

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 3:
        infile, outfile = sys.argv[1:]
        program = readIn(infile)
        results = pipeline(program)
        log(results, infile, outfile)
        program = str(results[-1])
        writeOut(program, outfile)
    else:
        print('usage:\n  python3 -m compiler source_file target_file')
        
