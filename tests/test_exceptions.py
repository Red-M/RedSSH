import unittest
import redssh

class RedSSHUnitTest(unittest.TestCase):

    def test_example_exception(self):
        redssh.exceptions.ExampleException()


if __name__ == '__main__':
    unittest.main()

