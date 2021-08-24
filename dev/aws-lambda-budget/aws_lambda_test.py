from unittest import TestCase
from aws_lambda import handle_message, handle_budget


class LambdaTest(TestCase):
    def test_handle_message(self):
        with open('./aws_lambda_test.py', 'r') as f:
            message = f.read()

        actual = handle_message(message)
        expected = 'test-a'

        self.assertEqual(actual, expected)

    def test_handle_budget(self):
        user_name = 'test-a'
        handle_budget(user_name)
        self.assertTrue(True)
