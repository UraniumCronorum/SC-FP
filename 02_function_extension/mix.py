
from Languages import R

i=6
j=-7

program = R.Program(R.Let((R.Var('x'), R.Int(i)),
                                      R.Sum(R.Var('x'),
                                            R.Let((R.Var('x'), R.Negative(R.Int(j))),
                                                  R.Var('x')))))
