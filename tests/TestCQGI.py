"""
    Tests CQGI functionality

    Currently, this includes:
       Parsing a script, and detecting its available variables
       Altering the values at runtime
       defining a build_object function to return results
"""

from cadquery import cqgi
from tests import BaseTest
import textwrap

TESTSCRIPT = textwrap.dedent(
    """
        height=2.0
        width=3.0
        (a,b) = (1.0,1.0)
        foo="bar"

        result =  "%s|%s|%s|%s" % ( str(height) , str(width) , foo , str(a) )
        build_object(result)
    """
)


class TestCQGI(BaseTest):
    def test_parser(self):
        model = cqgi.CQModel(TESTSCRIPT)
        metadata = model.metadata

        self.assertEquals(set(metadata.parameters.keys()), {'height', 'width', 'a', 'b', 'foo'})

    def test_build_with_empty_params(self):
        model = cqgi.CQModel(TESTSCRIPT)
        result = model.build()

        self.assertTrue(result.success)
        self.assertTrue(len(result.results) == 1)
        self.assertTrue(result.results[0] == "2.0|3.0|bar|1.0")

    def test_build_with_different_params(self):
        model = cqgi.CQModel(TESTSCRIPT)
        result = model.build({'height': 3.0})
        self.assertTrue(result.results[0] == "3.0|3.0|bar|1.0")

    def test_build_with_exception(self):
        badscript = textwrap.dedent(
            """
                raise ValueError("ERROR")
            """
        )

        model = cqgi.CQModel(badscript)
        result = model.build({})
        self.assertFalse(result.success)
        self.assertIsNotNone(result.exception)
        self.assertTrue(result.exception.message == "ERROR")

    def test_that_invalid_syntax_in_script_fails_immediately(self):
        badscript = textwrap.dedent(
            """
                this doesnt even compile
            """
        )

        with self.assertRaises(Exception) as context:
            model = cqgi.CQModel(badscript)

        self.assertTrue('invalid syntax' in context.exception)

    def test_that_two_results_are_returned(self):
        script = textwrap.dedent(
            """
                h = 1
                build_object(h)
                h = 2
                build_object(h)
            """
        )

        model = cqgi.CQModel(script)
        result = model.build({})
        self.assertEquals(2, len(result.results))
        self.assertEquals(1, result.results[0])
        self.assertEquals(2, result.results[1])

    def test_that_assinging_number_to_string_works(self):
        script = textwrap.dedent(
            """
                h = "this is a string"
                build_object(h)
            """
        )
        result = cqgi.execute(script, {'h': 33.33})
        self.assertEquals(result.results[0], "33.33")

    def test_that_assigning_string_to_number_fails(self):
        script = textwrap.dedent(
            """
                h = 20.0
                build_object(h)
            """
        )
        result = cqgi.execute(script, {'h': "a string"})
        self.assertTrue(isinstance(result.exception, cqgi.InvalidParameterError))

    def test_that_assigning_unknown_var_fails(self):
        script = textwrap.dedent(
            """
                h = 20.0
                build_object(h)
            """
        )

        result = cqgi.execute(script, {'w': "var is not there"})
        self.assertTrue(isinstance(result.exception, cqgi.InvalidParameterError))

    def test_that_not_calling_build_object_raises_error(self):
        script = textwrap.dedent(
            """
                h = 20.0
            """
        )
        result = cqgi.execute(script)
        self.assertTrue(isinstance(result.exception, cqgi.NoOutputError))

    def test_that_cq_objects_are_visible(self):
        script = textwrap.dedent(
            """
                r = cadquery.Workplane('XY').box(1,2,3)
                build_object(r)
            """
        )

        result = cqgi.execute(script)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.first_result)