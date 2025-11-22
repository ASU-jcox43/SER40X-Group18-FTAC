import unittest
import json

from jurisdiction_scorer import import_model


class MyTestCase(unittest.TestCase):
    rex = import_model("scoring_models/test_expressions.json")

    def test_exp1(self):
        self.assertRegex('"500."', self.rex["1"])
        self.assertRegex('"1."', self.rex["1"])
        self.assertRegex("\"892.\"", self.rex["1"])
        self.assertNotRegex('62.', self.rex["1"])
        self.assertNotRegex('"1"', self.rex["1"])
        self.assertNotRegex('"aop"', self.rex["1"])
        self.assertNotRegex('"."', self.rex["1"])
        self.assertNotRegex('"661', self.rex["1"])
        self.assertNotRegex('"', self.rex["1"])
        self.assertNotRegex('"%.', self.rex["1"])

    def test_exp2(self):
        self.assertRegex('\\rfa_234', self.rex["2"])
        self.assertRegex('\\gds', self.rex["2"])
        self.assertNotRegex('fs\\', self.rex["2"])
        self.assertNotRegex('dsanbn', self.rex["2"])
        self.assertNotRegex('\\', self.rex["2"])
        self.assertNotRegex('hhh', self.rex["2"])
        self.assertNotRegex('*sda1', self.rex["2"])

    def test_exp3(self):
        self.assertRegex('\'2. f\'', self.rex["3"])
        self.assertRegex("'3. $'", self.rex["3"])
        self.assertRegex("'6. \\'", self.rex["3"])
        self.assertNotRegex('\'\'', self.rex["3"])
        self.assertNotRegex('\'% .54\'', self.rex["3"])
        self.assertNotRegex("'43. &'", self.rex["3"])

if __name__ == '__main__':
    unittest.main()
