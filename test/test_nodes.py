import includes_for_tests
import os
import sys
import unittest

# Load NCPA
sys.path.append(os.path.join(os.path.dirname(__file__), '../agent/'))
import listener.server

class EmptyNode(object):
    def __init__(self, name):
        self.name = name

class TestParentNode(unittest.TestCase):

    def setUp(self):
        listener.server.__INTERNAL__ = True
        self.n = listener.nodes.ParentNode('testing')

    def test_init(self):
        test_nodes = [EmptyNode(x) for x in ('bingo', 'bongo')]
        p = listener.nodes.ParentNode('parent_testing', test_nodes)

        for node in test_nodes:
            self.assertTrue(node.name in p.children)
            self.assertEqual(node, p.children[node.name])

    def test_add_child(self):
        self.assertEqual(self.n.children, {})

        new_node_name = 'testing'
        new_node = EmptyNode(new_node_name)

        self.n.add_child(new_node)

        self.assertIn(new_node_name, self.n.children)

    def test_accessor_returns_a_node(self):
        test_node = listener.nodes.ParentNode('testing')
        self.n.add_child(test_node)

        self.assertIsInstance(self.n.accessor(['testing'], None, None, None), listener.nodes.ParentNode)
        self.assertIsInstance(self.n.accessor(['nonexistent'], None, None, None), listener.nodes.DoesNotExistNode)

    def test_accessor_returns_a_copy(self):
        test_node = listener.nodes.ParentNode('testing')
        self.n.add_child(test_node)

        self.assertIsNot(test_node, self.n.accessor(['testing'], None, None, None))

    def test_walk_returns_dict(self):
        self.assertIsInstance(self.n.walk(), dict)

    def test_run_check_returns_dict(self):
        self.assertIsInstance(self.n.run_check(), dict)

    def test_run_check_returns_valid_result(self):
        result = self.n.run_check()

        self.assertIn('stdout', result)
        self.assertIn('returncode', result)


class TestRunnableNode(unittest.TestCase):

    def setUp(self):
        self.node_name = 'testing'
        self.n = listener.nodes.RunnableNode(self.node_name, lambda: ('Ok', 1))

    def test_accessor_returns_copy(self):
        self.assertIsNot(self.n, self.n.accessor([], None, None, None))

    def test_walk_returns_dict(self):
        self.assertIsInstance(self.n.walk(), dict)

    def test_walk_returns_valid_response(self):
        response = self.n.walk()

        self.assertIn(self.node_name, response)
        self.assertEqual(len(response[self.node_name]), 2)

    def test_walk_passes_units(self):
        response = self.n.walk(unit='t')

        self.assertEqual(response[self.node_name][1], 't')

    def test_set_unit(self):
        self.n.set_unit('b', {})
        self.assertEqual(self.n.unit, 'b')

    def test_set_unit_with_kwargs(self):
        self.n.set_unit('b', {'unit': 'k'})
        self.assertEqual(self.n.unit, 'k')

    def test_get_adjusted_scale(self):
        values = self.n.get_adjusted_scale([0], {})
        self.assertEqual(values, [0])

    def test_get_adjusted_scale_with_unit(self):
        self.n.adjust_scale = lambda x, y: ([z+1 for z in x], 'b')
        values = self.n.get_adjusted_scale([0], {'units': 'k'})

        self.assertEqual(values, [0])
        self.assertEqual(self.n.unit, '')

    def test_set_warning(self):
        self.n.set_warning({'warning': [0]})
        self.assertEqual([0], self.n.warning)

        self.n.set_warning({})
        self.assertEqual('', self.n.warning)

    def test_set_critical(self):
        self.n.set_critical({'critical': [0]})
        self.assertEqual([0], self.n.critical)

        self.n.set_critical({})
        self.assertEqual('', self.n.critical)

    def test_set_title(self):
        self.n.set_title({})
        self.assertEqual(self.n.title, self.node_name)

        self.n.set_title({'title': ['title']})
        self.assertEqual(self.n.title, 'title')

    def test_set_perfdata_label(self):
        self.n.set_perfdata_label({'perfdata_label': [0]})
        self.assertEqual(0, self.n.perfdata_label)

        self.n.set_perfdata_label({})
        self.assertEqual(None, self.n.perfdata_label)

    def test_run_check(self):
        result = self.n.run_check()
        self.assertIsInstance(result, dict)


if __name__ == '__main__':
    unittest.main()