
from Languages import R

r_dict = {
    'program' : R.Program,
    '+' : R.Sum,
    '-' : R.Negative,
    'let': R.Let
    }
    
def parse_sexpr(source):
    out = [[]]
    token = ''
    for char in source:
        if char in '([':
            if token:
                out[-1].append(token)
            out.append([])
            token = ''
        elif char in '])':
            if token:
                out[-1].append(token)
            l = out.pop()
            out[-1].append(l)
            token = ''
        else:
            if char in ' \t\n':
                if token:
                    out[-1].append(token)
                    token = ''
            else:
                token += char
    if token:
        out[-1].append(token)
    assert len(out) == 1
    return out[0]

def parse_R(ast):
    if isinstance(ast, str):
        try:
            return R.Int(int(ast))
        except ValueError:
            return R.Var(ast)
    head, rest = ast[0], ast[1:]
    if head == 'program':
        assert len(rest) == 1
        return R.Program(parse_R(rest[0]))
    elif head == '+':
        assert len(rest) == 2
        return R.Sum(parse_R(rest[0]), parse_R(rest[1]))
    elif head == '-':
        assert len(rest) == 1
        return R.Negative(parse_R(rest[0]))
    elif head == 'let':
        assert len(rest) == 2
        bindings, body = rest
        assert len(bindings) == 1
        binding = bindings[0]
        assert len(binding) == 2
        return R.Let(binding = (parse_R(binding[0]), parse_R(binding[1])),
                     body = parse_R(body))
    else:
        raise ValueError (head)

def parse_R_from_string(source):
    asts = parse_sexpr(source)
    assert len(asts) == 1
    ast = asts[0]
    assert ast[0] == 'program'
    return parse_R(ast)
