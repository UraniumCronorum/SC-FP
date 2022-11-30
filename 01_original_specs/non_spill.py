
from Languages import R
import string

def helper(_vars):
    if _vars:
        var = _vars[0]
        rest = _vars[1:]
        i = len(_vars)
        out = R.Let((R.Var(var), R.Int(i)),
                    R.Sum(R.Var(var),
                          helper(rest)))
        out.checkForm()
        return out
    return R.Int(0)

program = R.Program(helper(string.ascii_lowercase[:13]))
