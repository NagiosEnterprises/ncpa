import listener
import unittest


class TestPSApi(unittest.TestCase):

    def test_get_disk_nodes(self):
        disk_node = listener.psapi.get_disk_node([])
        self.assertIsInstance(disk_node, listener.nodes.ParentNode)

    def test_get_system_node(self):
        if_node = listener.psapi.get_system_node()
        self.assertIsInstance(if_node, listener.nodes.ParentNode)

    def test_get_cpu_node(self):
        cpu_node = listener.psapi.get_cpu_node()
        self.assertIsInstance(cpu_node, listener.nodes.ParentNode)

    def test_get_memory_node(self):
        memory_node = listener.psapi.get_cpu_node()
        self.assertIsInstance(memory_node, listener.nodes.ParentNode)

    def test_get_interface_node(self):
        if_node = listener.psapi.get_interface_node()
        self.assertIsInstance(if_node, listener.nodes.ParentNode)

    def test_get_plugins_node(self):
        plugin_node = listener.psapi.get_plugins_node()
        self.assertIsInstance(plugin_node, listener.nodes.ParentNode)

    def test_get_user_node(self):
        user_node = listener.psapi.get_user_node()
        self.assertIsInstance(user_node, listener.nodes.ParentNode)

    def test_get_root_node(self):
        root_node = listener.psapi.get_root_node([])
        self.assertIsInstance(root_node, listener.nodes.ParentNode)
