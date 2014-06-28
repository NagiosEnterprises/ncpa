import nodes
import unittest


def get_nodes(names):
    class TestNode(object):
        def __init__(self, name):
            self.name = name

    lat = []

    for name in names:
        x = TestNode(name)
        lat.append(x)

    return lat


class TestParentNode(unittest.TestCase):
    def setUp(self):
        self.n = nodes.ParentNode('testing')

    def test_init(self):
        testing_set = ['bingo', 'bongo']
        test_nodes = get_nodes(names=testing_set)

        p = nodes.ParentNode('parent_testing', test_nodes)

        for node in test_nodes:
            self.assertTrue(node.name in p.children)
            self.assertEquals(node, p.children[node.name])


if __name__ == '__main__':
    unittest.main()