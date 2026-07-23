import includes_for_tests
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Load NCPA
sys.path.append(os.path.join(os.path.dirname(__file__), '../agent/'))
import listener.server
import listener.psapi


def _mock_disk_counter():
    counter = MagicMock()
    counter.read_time = 1
    counter.write_time = 2
    counter.read_count = 3
    counter.write_count = 4
    counter.read_bytes = 5
    counter.write_bytes = 6
    return counter


class TestPSApi(unittest.TestCase):

    def test_get_disk_nodes(self):
        disk_node = listener.psapi.get_disk_node([])
        self.assertIsInstance(disk_node, listener.nodes.ParentNode)

    @patch('listener.psapi.ps.disk_partitions', return_value=[])
    @patch('listener.psapi.ps.disk_io_counters')
    def test_get_disk_node_calls_disk_io_counters_once(
        self, mock_disk_io_counters, mock_disk_partitions
    ):
        mock_disk_io_counters.return_value = {
            'sda': _mock_disk_counter(),
            'sdb': _mock_disk_counter(),
            'sdc': _mock_disk_counter(),
        }

        disk_node = listener.psapi.get_disk_node([])

        mock_disk_io_counters.assert_called_once_with(perdisk=True)
        physical = disk_node.children['physical']
        self.assertEqual(len(physical.children), 3)
        self.assertIn('sda', physical.children)
        self.assertIn('sdb', physical.children)
        self.assertIn('sdc', physical.children)

    @patch('listener.psapi.ps.disk_usage')
    def test_mountpoint_nodes_call_disk_usage_once_per_walk(self, mock_disk_usage):
        mock_disk_usage.return_value = MagicMock(
            total=100, used=40, free=60, percent=40.0
        )
        partition = MagicMock()
        partition.mountpoint = '/'
        partition.device = '/dev/sda1'
        partition.fstype = 'ext4'
        partition.opts = 'rw'
        partition.maxfile = 255
        partition.maxpath = 4096

        node = listener.psapi.make_mountpoint_nodes(partition)
        node.walk()

        mock_disk_usage.assert_called_once_with('/')

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
