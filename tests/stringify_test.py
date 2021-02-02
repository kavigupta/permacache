import unittest
import json

from permacache import stringify


class StringifyTest(unittest.TestCase):
    def test_stringify_json(self):
        self.assertEqual("2", stringify(2))
        self.assertEqual("[2, 3]", stringify([2, 3]))
        self.assertEqual('{"a": 3}', stringify({"a": 3}))

    def test_stringify_attrs(self):
        import attr

        @attr.s
        class X:
            y = attr.ib()

        self.assertEqual(
            json.dumps({".attr.__name__": "X", "y": "hello"}), stringify(X("hello"))
        )
