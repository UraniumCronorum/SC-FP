
from hypothesis import given, example, note
import unittest
from unittest import mock
import random
import itertools

import hypothesis_R as _R
from compiler import *

class RTest(unittest.TestCase):

    @given(_R.programs)
    def testWellFormed(self, p):
        p.checkForm()

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


if __name__ == '__main__':
    unittest.main()
