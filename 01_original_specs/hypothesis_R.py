
from hypothesis.strategies import *
from Languages import R

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

programs = builds(R.Program, expressions)

if __name__ == '__main__':
    for i in range(8):
        e = programs.example()
        print(repr(e))
        print(e)


