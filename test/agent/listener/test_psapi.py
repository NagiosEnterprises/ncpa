__author__ = 'nscott'

import nodes
import psapi
import unittest


class TestPSApi(unittest.TestCase):

    def test_get_disk_nodes(self):
        disk_node = psapi.get_disk_node()
        self.assertIsInstance(disk_node, nodes.ParentNode)

    def test_get_system_node(self):
        if_node = psapi.get_system_node()
        self.assertIsInstance(if_node, nodes.ParentNode)

    def test_get_cpu_node(self):
        cpu_node = psapi.get_cpu_node()
        self.assertIsInstance(cpu_node, nodes.ParentNode)

    def test_get_memory_node(self):
        memory_node = psapi.get_cpu_node()
        self.assertIsInstance(memory_node, nodes.ParentNode)

    def test_get_interface_node(self):
        if_node = psapi.get_interface_node()
        self.assertIsInstance(if_node, nodes.ParentNode)

    def test_get_agent_node(self):
        plugin_node = psapi.get_agent_node()
        self.assertIsInstance(plugin_node, nodes.ParentNode)

    def test_get_user_node(self):
        user_node = psapi.get_user_node()
        self.assertIsInstance(user_node, nodes.ParentNode)

    def test_get_root_node(self):
        root_node = psapi.get_root_node()
        self.assertIsInstance(root_node, nodes.ParentNode)
