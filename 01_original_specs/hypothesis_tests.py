
from hypothesis import given, example, note
import unittest
from unittest import mock
import random
import itertools

import hypothesis_R as _R
from compiler import *
from parsers import parse_R_from_string

class RTest(unittest.TestCase):

    @given(_R.programs)
    def testWellFormed(self, p):
        p.checkForm()

    # testing repr()
    @given(_R.programs)
    def testRepr(self, p):
        pp = eval(repr(p))
        # I didn't implement __eq__ so I can't easily check that they're
        # identical; this will suffice
        assert repr(pp) == repr(p)
        assert str(pp) == str(p)

    # testing parser
    @given(_R.programs)
    def testParser(self, p):
        pp = parse_R_from_string(str(p))
        assert repr(pp) == repr(p)
        assert str(pp) == str(p)

    # testing evaluation
    @given(_R.programs)
    def testEval(self, p):
        with mock.patch('_sys.readInt', return_value = random.randint(0,100)):
            try:
                result = p.interpret()
                assert isinstance(result, int)
            except R.VarNotDefined:
                pass



class UniquifyTest(unittest.TestCase):

    @given(_R.programs)
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

class PipelineTest(unittest.TestCase):
    languages = R, R_uniq, C_flat, X_var, X_approx, X

    @given(_R.programs)
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

    @given(_R.saferPrograms())
    #@example(p=R.Program(R.Let((R.Var('a'), R.Int(0)), R.Let((R.Var('a'), R.Sum(R.Read(), R.Let((R.Var('a'), R.Int(0)), R.Var('a')))), R.Var('a')))))
    def test_partial_pipeline(self, p):
        pipeline_results, e = partial_pipeline(p)
        if e is not None:
            if isinstance(e, R.VarNotDefined):
                return # ignore
            elif isinstance(e, TypeError):
                if e.args[0] != 'select_instr (assign): (read)':
                    raise e
            else:
                raise e

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
