
from hypothesis import given
from hypothesis_R import *
from unittest import mock
import itertools

example_a = R.Let((R.Var('x'), R.Int(1)), R.Int(1))
example_b = R.Let((R.Var('x'), R.Int(2)), R.Int(1))

@composite
def get_example_pair(draw):
    b1 = draw(tuples(builds(R.Var, varnames), builds(R.Int, integers())))
    b2 = draw(tuples(builds(R.Var, varnames), builds(R.Int, integers())))
    body = draw(expressions)
    assignVarNames(body)
    out = (R.Let(b1, body), R.Let(b2, body))
    try:
        with mock.patch('_sys.readInt', result=R.Int(5)):
            assume(out[0].interpret({}) == out[1].interpret({}))
    except R.VarNotDefined:
        assume(False)
    return out

@composite
def contexts(draw):
    binding = (R.Var('expr'), None)
    body = draw(expressions)
    assignVarNames(body, defined={'expr'})
    out = R.Let(binding, body)
    return R.Program(out)

def apply_context(expression, context):
    ''' Insert expression into context in-place'''
    new_binding = (R.Var('expr'), expression)
    context.body.binding = new_binding

@given(contexts())
def simpleTest(ctx):
    record = []
    def gen():
        while True:
            n = random.randint(0,100)
            record.append(n)
            yield n
    apply_context(example_a, ctx)
    with mock.patch('_sys.readInt', side_effect = gen()):
        result_a = ctx.interpret()
    apply_context(example_b, ctx)
    with mock.patch('_sys.readInt',
                    side_effect=itertools.chain(record, gen())):
        result_b = ctx.interpret()
    assert result_a == result_b

@given(get_example_pair(), contexts())
def anotherTest(pair, ctx):
    expr_a, expr_b = pair

    record = []
    def gen():
        while True:
            n = random.randint(0,100)
            record.append(n)
            yield n
    apply_context(expr_a, ctx)
    with mock.patch('_sys.readInt', side_effect = gen()):
        result_a = ctx.interpret()
    apply_context(expr_b, ctx)
    with mock.patch('_sys.readInt',
                    side_effect=itertools.chain(record, gen())):
        result_b = ctx.interpret()
    assert result_a == result_b


if __name__ == '__main__':
    simpleTest()
    anotherTest()
