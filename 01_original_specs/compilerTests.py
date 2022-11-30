################################
# Author: Wesley Nuzzo

import unittest
from unittest import mock
from compiler import *

import string

################################
# Uniquify Tests
class TestUniquify(unittest.TestCase):
    ''' Test cases for the uniquify function'''

    def checkProgram(self, program):
        ''' Check that the result of evaluating the program is the same,
        and that nested lets do not redefine the same variables.'''
        unique = uniquify(program)

        self.assertIsInstance(unique, R_uniq.Program)
        self.assertEqual(program.interpret(), unique.interpret())
    
    def testIO(self):
        read = R.Program(R.Read())
        with mock.patch('_sys.readInt', return_value = 1):
            self.checkProgram(read)

    def testLiterals(self):
        for i in range(-8, 8):
            num = R.Program(R.Int(i))
            self.checkProgram(num)

    def testOperators(self):
        ''' Test uniquification of operators with and without contained lets.'''
        # unary operators
        for i in range(-8,8):
            neg = R.Program(R.Negative(R.Int(i)))
            negLet = R.Program(R.Negative(R.Let((R.Var('x'),
                                                 R.Int(i)),
                                                R.Var('x'))))
            self.checkProgram(neg)
            self.checkProgram(negLet)

            # binary operators
            for j in range(-8,8):
                plus = R.Program(R.Sum(R.Int(i),
                                        R.Int(j)))
                plusLet = R.Program(R.Sum(R.Let((R.Var('x'),
                                                 R.Int(i)),
                                                R.Var('x')),
                                          R.Negative(R.Let((R.Var('x'),
                                                            R.Int(j)),
                                                           R.Var('x')))))
                self.checkProgram(plus)
                self.checkProgram(plusLet)

    def testFrames(self):
        ''' Variables defined in inner frames should not be defined in outer frames.

        Also check that the compiler fails when the input involves undefined
        variables.'''

        # Make sure programs with undefined variables are not compiled
        with self.assertRaises(R.VarNotDefined):
            var = R.Program(R.Var('x'))
            uniquify(var)
        for i in range(-8, 8):
            let = R.Program(R.Let((R.Var('x'),
                                   R.Int(i)),
                                  R.Var('x')))
            nest = R.Program(R.Let((R.Var('x'),
                                    R.Int(i)),
                                   R.Let((R.Var('x'),
                                          R.Int(i)),
                                         R.Var('x'))))
            self.checkProgram(let)
            self.checkProgram(nest)


################################
# Flatten Tests
class TestFlatten(unittest.TestCase):
    ''' Check the operation of the flatten function'''

    def checkProgram(self, program, p=False):
        ''' Check that the result of evaluating the program is the same,
        and that the flattened program is a flat C_flat program.'''
        circle = circleFlatten(program)
        self.assertEqual(program.interpret(), circle.interpret())
        self.assertIsInstance(circle, C_flat.Program)

##        square = squareFlatten(program)
##        self.assertEqual(program.itterpret(), square.interpret())
##        self.assertIsInstance(square, C_flat.Program)

    def testIO(self):
        read = R_uniq.Program(R_uniq.Read())
        with mock.patch('_sys.readInt', return_value = 1):
            self.checkProgram(read)

    def testLiterals(self):
        for i in range(-8, 8):
            num = R_uniq.Program(R_uniq.Int(i))
            self.checkProgram(num)

    def testOperators(self):
        ''' Test uniquification of operators with and without contained lets.'''
        # unary operators
        for i in range(-8,8):
            neg = R_uniq.Program(R_uniq.Negative(R_uniq.Int(i)))
            negLet = R_uniq.Program(R_uniq.Negative(R_uniq.Let((R_uniq.Var('x'),
                                                                R_uniq.Int(i)),
                                                               R_uniq.Var('x'))))
            self.checkProgram(neg)
            self.checkProgram(negLet)

           # binary operators
            for j in range(-8,8):
                plus = R_uniq.Program(R_uniq.Sum(R_uniq.Int(i),
                                        R_uniq.Int(j)))
                plusLet = R_uniq.Program(R_uniq.Sum(R_uniq.Let((R_uniq.Var('x'),
                                                                R_uniq.Int(i)),
                                                               R_uniq.Var('x')),
                                          R_uniq.Negative(R_uniq.Let((R_uniq.Var('x'),
                                                                      R_uniq.Int(j)),
                                                                     R_uniq.Var('x')))))
                self.checkProgram(plus)
                self.checkProgram(plusLet)

    def testFrames(self):

        for i in range(-8, 8):
            let = R_uniq.Program(R_uniq.Let((R_uniq.Var('x'),
                                             R_uniq.Int(i)),
                                            R_uniq.Var('x')))
            nest = R_uniq.Program(R_uniq.Let((R_uniq.Var('x'),
                                              R_uniq.Int(i)),
                                             R_uniq.Let((R_uniq.Var('y'),
                                                         R_uniq.Int(i)),
                                                        R_uniq.Var('x'))))
            self.checkProgram(let)
            self.checkProgram(nest)


################################
# Instruction Selection Tests
class TestSelectInstruction(unittest.TestCase):

    def checkProgram(self, program):
        result = select_instr(program)
        self.assertEqual(program.interpret(), result.interpret())
        self.assertIsInstance(result, X_var.Program)

    def testLiterals(self):
        for i in range(-8, 8):
            num = C_flat.Program({'x'},
                                 C_flat.Assign(C_flat.Var('x'),
                                               C_flat.Int(i)),
                                 C_flat.Return(C_flat.Var('x')))
            self.checkProgram(num)

    def testOperators(self):
        for i in range(-8, 8):
            neg = C_flat.Program({'i', '-i'},
                                 C_flat.Assign(C_flat.Var('i'), C_flat.Int(i)),
                                 C_flat.Assign(C_flat.Var('-i'),
                                               C_flat.Negative(C_flat.Var('i'))),
                                 C_flat.Return(C_flat.Var('-i')))
            self.checkProgram(neg)
            for j in range(-8, 8):
                plus = C_flat.Program({'i', 'j', 'i+j'},
                                      C_flat.Assign(C_flat.Var('i'),
                                                    C_flat.Int(i)),
                                      C_flat.Assign(C_flat.Var('j'),
                                                    C_flat.Int(j)),
                                      C_flat.Assign(C_flat.Var('i+j'),
                                                    C_flat.Sum(C_flat.Var('i'),
                                                               C_flat.Var('j'))),
                                      C_flat.Return(C_flat.Var('i+j')))
                self.checkProgram(plus)

    def testFrames(self):
        for i in range(-8,8):
            xy = C_flat.Program({'x', 'y'},
                                C_flat.Assign(C_flat.Var('x'), C_flat.Int(i)),
                                C_flat.Assign(C_flat.Var('y'), C_flat.Var('x')),
                                C_flat.Return(C_flat.Var('y')))
            self.checkProgram(xy)
            for j in range(-8,8):
                xx = C_flat.Program({'x'},
                                    C_flat.Assign(C_flat.Var('x'), C_flat.Int(i)),
                                    C_flat.Assign(C_flat.Var('x'), C_flat.Int(j)),
                                    C_flat.Return(C_flat.Var('x')))
                self.checkProgram(xx)
                                

################################
# Assign Homes Tests
class TestAssignHomes(unittest.TestCase):

    def checkProgram(self, program):
        program.checkForm()
        result = assign_homes(program)
        self.assertEqual(program.interpret(), result.interpret())
        # Check that no variables are used
        self.assertIsInstance(result, X_approx.Program)

    ########
    # Tests
    def testLiterals(self):
        for i in range(-8, 8):
            x = X_var.Program(X_var.Movq(X_var.Int(i),
                                         X_var.Var('retvar')),
                              X_var.Retq())
            self.checkProgram(x)

    def testOperators(self):
        for i in range(-8, 8):
            neg = X_var.Program(X_var.Movq(X_var.Int(i), X_var.Var('retvar')),
                                X_var.Negq(X_var.Var('retvar')),
                                X_var.Retq())
            self.checkProgram(neg)
            for j in range(-8, 8):
                add = X_var.Program(X_var.Movq(X_var.Int(i), X_var.Var('retvar')),
                                    X_var.Addq(X_var.Int(j), X_var.Var('retvar')),
                                    X_var.Retq())
                sub = X_var.Program(X_var.Movq(X_var.Int(i), X_var.Var('retvar')),
                                    X_var.Subq(X_var.Int(j), X_var.Var('retvar')),
                                    X_var.Retq())
                self.checkProgram(add)
                self.checkProgram(sub)

    def testFrames(self):
        for i in range(8):
            for j in range(8):
                for k in range(8):
                    prog = X_var.Program(X_var.Movq(X_var.Int(i), X_var.Var('x')),
                                         X_var.Movq(X_var.Int(j), X_var.Var('y')),
                                         X_var.Movq(X_var.Int(k), X_var.Var('z')),
                                         X_var.Addq(X_var.Var('x'), X_var.Var('y')),
                                         X_var.Addq(X_var.Var('y'), X_var.Var('z')),
                                         X_var.Addq(X_var.Var('z'), X_var.Var('x')),
                                         X_var.Movq(X_var.Var('x'), X_var.Var('retvar')),
                                         X_var.Retq())
                    self.checkProgram(prog)

    def testSpill(self):
        instrs = []
        for i, char in enumerate(string.ascii_lowercase):
            instrs.append(X_var.Movq(X_var.Int(i),
                                     X_var.Var(char)))
        instrs.append(X_var.Movq(X_var.Int(0),
                                 X_var.Var('retvar')))
        for char in string.ascii_lowercase:
            instrs.append(X_var.Addq(X_var.Var(char),
                                     X_var.Var('retvar')))
        instrs.append(X_var.Retq())
        prog = X_var.Program(*instrs)
        result = assign_homes(prog)
        self.checkProgram(prog)

class TestPatch(unittest.TestCase):

    def checkProgram(self, program):
        result = patch(program)
        self.assertEqual(program.interpret(), result.interpret())
        self.assertIsInstance(result, X.Program)

    #######
    # Tests
    def testLiterals(self): 
        for i in range(-8, 8):
            x = X_approx.Program(X_approx.Movq(X_approx.Int(i),
                                               X_approx.Reg.RAX),
                                 X_approx.Retq())
            self.checkProgram(x)

    def testOperators(self):
        for i in range(-8, 8):
            neg = X_approx.Program(X_approx.Movq(X_approx.Int(i),
                                                 X_approx.Reg.RAX),
                                   X_approx.Negq(X_approx.Reg.RAX),
                                   X_approx.Retq())
            self.checkProgram(neg)
            for j in range(-8, 8):
                add = X_approx.Program(X_approx.Movq(X_approx.Int(i),
                                                     X_approx.Reg.RAX),
                                       X_approx.Addq(X_approx.Int(j),
                                                     X_approx.Reg.RAX),
                                       X_approx.Retq())
                sub = X_approx.Program(X_approx.Movq(X_approx.Int(i),
                                                     X_approx.Reg.RAX),
                                       X_approx.Subq(X_approx.Int(j),
                                                     X_approx.Reg.RAX),
                                       X_approx.Retq())
                self.checkProgram(add)
                self.checkProgram(sub)

    def testFrames(self):
        for i in range(8):
            for j in range(8):
                prog = X_approx.Program(X_approx.Movq(X_approx.Int(i*j),
                                                      X_approx.Addr(X_approx.Reg.RBP, -4*i)),
                                        X_approx.Movq(X_approx.Addr(X_approx.Reg.RBP, -4*i),
                                                      X_approx.Addr(X_approx.Reg.RBP, -4*j)),
                                        X_approx.Movq(X_approx.Addr(X_approx.Reg.RBP, -4*j),
                                                      X_approx.Reg.RAX),
                                        X_approx.Retq())
                prog.checkForm()
                self.checkProgram(prog)


class TestPipeline(unittest.TestCase):

    def checkProgram(self, program, a=False):
        results = pipeline(program)
        languages = R, R_uniq, C_flat, X_var, X_approx, X
        
        for i, result in enumerate(results):
            if a:
                print(result)
            
            self.assertEqual(program.interpret(),
                             result.interpret())
            self.assertIsInstance(result, languages[i].Program)
            
    def testLiterals(self):
        for i in range(-8, 8):
            num = R.Program(R.Int(i))
            self.checkProgram(num)

    def testOperators(self):
        for i in range(-8,8):
            neg = R.Program(R.Negative(R.Int(i)))
            self.checkProgram(neg)

            # binary operators
            for j in range(-8,8):
                plus = R.Program(R.Sum(R.Int(i),
                                       R.Int(j)))
                self.checkProgram(plus)

    def testFrames(self):
        # Make sure programs with undefined variables are not compiled
        with self.assertRaises(R.VarNotDefined):
            var = R.Program(R.Var('x'))
            uniquify(var)
        # May want to add a more elaborate generator for this
        for i in range(-8, 8):
            let = R.Program(R.Let((R.Var('x'), R.Int(i)),
                                  R.Var('x')))
            nest = R.Program(R.Let((R.Var('x'), R.Int(i)),
                                   R.Let((R.Var('x'), R.Int(i)),
                                         R.Var('x'))))
            self.checkProgram(let)
            self.checkProgram(nest)

    def testMix(self):
        for i in range(-8, 8):
            for j in range(-8, 8):
                mix = R.Program(R.Let((R.Var('x'), R.Int(i)),
                                      R.Sum(R.Var('x'),
                                            R.Let((R.Var('x'), R.Negative(R.Int(j))),
                                                  R.Var('x')))))
                self.checkProgram(mix, False)

    def testSpill(self):
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
        spill = R.Program(helper(string.ascii_lowercase))
        self.checkProgram(spill, False)

if __name__ == '__main__':
    unittest.main()
