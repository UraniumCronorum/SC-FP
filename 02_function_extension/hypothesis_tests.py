
from hypothesis import given, example, note
import unittest
from unittest import mock
import random
import itertools

import hypothesis_R as _R
from compiler import *

# p=R.Program([R.Function(R.Fname('a'), [], R.Call(R.Fname('a'), *())),
#              R.Function(R.Fname('b'), [], R.Int(0))],
#             R.Call(R.Fname('a'), *()))

@unittest.skip
class RTest(unittest.TestCase):

    # checking generator creates well-formed code
    @given(_R.programs)
    def testWellFormed(self, p):
        p.checkForm()
        
    @given(_R.programs)
    def testWellFormed(self, p):
        p.checkForm()
        
    @given(_R.safePrograms())
    def testWellFormedSafe(self, p):
        p.checkForm()

    # testing repr()
    @given(_R.programs)
    def testRepr(self, p):
        pp = eval(repr(p))
        # I didn't implement __eq__ so I can't easily check that they're
        # identical; this will suffice
        assert repr(pp) == repr(p)
        assert str(pp) == str(p)

    # testing str() and parse()
    # ...

    # testing the eval() method
    @given(_R.simple_programs)
    def testEval(self, p):
        with mock.patch('_sys.readInt', return_value = random.randint(0,100)):
            try:
                result = p.interpret()
                assert isinstance(result, int)
            except R.VarNotDefined:
                pass

    ####
    # these tests run very slowly w/ old definition

    @given(_R.saferPrograms())
    def testWellFormedSafer(self, p):
        p.checkForm()

    @given(_R.saferPrograms())
    def testEvalSafer(self, p):
        with mock.patch('_sys.readInt', return_value = random.randint(0,100)):
            try:
                result = p.interpret()
                assert isinstance(result, int)
            except RecursionError: # python builtin recursion error
                pass

class UniquifyTest(unittest.TestCase):

    @given(_R.simple_programs)
    def test_uniquify(self, p):
        try:
            compiled_program = uniquify(p)
        except R.VarNotDefined:
            return
        assert isinstance(compiled_program, R_uniq.Program)
        compiled_program.checkForm()

        record = []
        def gen():
            while True:
                n = random.randint(0,100)
                record.append(n)
                yield n
        with mock.patch('_sys.readInt', side_effect = gen()):
            source_result = p.interpret()
        with mock.patch('_sys.readInt', side_effect=itertools.chain(record, gen())):
            target_result = compiled_program.interpret()
        assert source_result == target_result

    @given(_R.programs)
    def test_uniquify_form(self, p):
        try:
            compiled_program = uniquify(p)
        except (R.VarNotDefined, R.FunctionNotDefined):
            return
        assert isinstance(compiled_program, R_uniq.Program)
        compiled_program.checkForm()

##        record = []
##        def gen():
##            while True:
##                n = random.randint(0,100)
##                record.append(n)
##                yield n
##        with mock.patch('_sys.readInt', side_effect = gen()):
##            source_result = p.interpret()
##        with mock.patch('_sys.readInt', side_effect=itertools.chain(record, gen())):
##            target_result = compiled_program.interpret()
##        assert source_result == target_result

class PipelineTest(unittest.TestCase):
    languages = R, R_uniq, C_flat, X_var, X_approx, X

    @given(_R.saferPrograms())
    def test_pipeline(self, p):
        try:
            pipeline_results = pipeline(p)
        except R.VarNotDefined:
            return
        except TypeError:
            return

        # check for correct language
        for lang, program in zip(self.languages, pipeline_results):
            assert isinstance(program, lang.Program)
            program.checkForm()

        # check behavior
        record = []
        def gen():
            while True:
                n = random.randint(0,100)
                record.append(n)
                yield n
        with mock.patch('_sys.readInt', side_effect = gen()):
            source_result = p.interpret()

        for program in pipeline_results:
            with mock.patch('_sys.readInt',
                            side_effect=itertools.chain(record, gen())):
                target_result = program.interpret()
            assert source_result == target_result


if __name__ == '__main__':
    unittest.main()
