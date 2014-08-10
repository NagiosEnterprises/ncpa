import nodes
import unittest


class TestNode(object):
        def __init__(self, name):
            self.name = name


class TestParentNode(unittest.TestCase):

    def setUp(self):
        self.n = nodes.ParentNode('testing')

    def test_init(self):
        test_nodes = [TestNode(x) for x in ('bingo', 'bongo')]
        p = nodes.ParentNode('parent_testing', test_nodes)

        for node in test_nodes:
            self.assertTrue(node.name in p.children)
            self.assertEquals(node, p.children[node.name])

    def test_add_child(self):
        self.assertEqual(self.n.children, {})

        new_node_name = 'testing'
        new_node = TestNode(new_node_name)

        self.n.add_child(new_node)

        self.assertIn(new_node_name, self.n.children)

    def test_accessor_returns_a_node(self):
        test_node = nodes.ParentNode('testing')
        self.n.add_child(test_node)

        self.assertIsInstance(self.n.accessor(['testing'], None), nodes.ParentNode)
        self.assertIsInstance(self.n.accessor(['nonexistent'], None), nodes.ParentNode)

    def test_accessor_returns_a_copy(self):
        test_node = nodes.ParentNode('testing')
        self.n.add_child(test_node)

        self.assertIsNot(test_node, self.n.accessor(['testing'], None))

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
        self.n = nodes.RunnableNode(self.node_name, lambda: ('Ok', 1))

    def test_accessor_returns_copy(self):
        self.assertIsNot(self.n, self.n.accessor([], None))

    def test_accessor_returns_error_on_extra_path(self):
        self.assertRaises(IndexError, self.n.accessor, ['extra'], None)

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

    def test_get_delta_values(self):
        values = self.n.get_delta_values([0], {})
        self.assertEqual(values, [0])

        self.n.deltaize_values = lambda x, y: ([z+1 for z in x], y)
        values = self.n.get_delta_values([0], {'delta': True})
        self.assertEqual(values, ([1], None))

    def test_get_adjusted_scale(self):
        values = self.n.get_adjusted_scale([0], {})
        self.assertEqual(values, [0])

    def test_get_adjusted_scale_with_unit(self):
        self.n.adjust_scale = lambda x, y: ([z+1 for z in x], 'b')
        values = self.n.get_adjusted_scale([0], {'units': 'k'})

        self.assertEqual(values, [1])
        self.assertEqual(self.n.unit, 'b')

    def test_set_warning(self):
        self.n.set_warning({'warning': [0]})
        self.assertEqual(0, self.n.warning)

        self.n.set_warning({})
        self.assertEqual('', self.n.warning)

    def test_set_critical(self):
        self.n.set_critical({'critical': [0]})
        self.assertEqual(0, self.n.critical)

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