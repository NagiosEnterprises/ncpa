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

    def test_parse_os_release_file(self):
        contents = (
            'NAME="Red Hat Enterprise Linux"\n'
            "ID=rhel\n"
            'PRETTY_NAME="Red Hat Enterprise Linux 9.2 (Plow)"\n'
            'VERSION_ID="9.2"\n'
            "# comment\n"
            "ID_LIKE=\"fedora\"\n"
        )
        data = listener.psapi.parse_os_release_file(contents)
        self.assertEqual(data["NAME"], "Red Hat Enterprise Linux")
        self.assertEqual(data["ID"], "rhel")
        self.assertEqual(data["PRETTY_NAME"], "Red Hat Enterprise Linux 9.2 (Plow)")
        self.assertEqual(data["VERSION_ID"], "9.2")
        self.assertEqual(data["ID_LIKE"], "fedora")
        self.assertNotIn("# comment", data)

    def test_get_os_release_node_builds_children(self):
        data = {
            "NAME": "Ubuntu",
            "ID": "ubuntu",
            "PRETTY_NAME": "Ubuntu 22.04.3 LTS",
            "VERSION_ID": "22.04",
            "VERSION_CODENAME": "jammy",
            "ID_LIKE": "debian",
        }
        node = listener.psapi.get_os_release_node(data)
        self.assertIsInstance(node, listener.nodes.ParentNode)
        self.assertEqual(node.name, "os_release")
        self.assertIn("name", node.children)
        self.assertIn("id", node.children)
        self.assertIn("pretty_name", node.children)
        self.assertIn("version_id", node.children)
        self.assertIn("version_codename", node.children)
        self.assertIn("id_like", node.children)

        walked = node.walk()
        self.assertEqual(
            walked,
            {
                "os_release": {
                    "name": "Ubuntu",
                    "id": "ubuntu",
                    "pretty_name": "Ubuntu 22.04.3 LTS",
                    "version_id": "22.04",
                    "version_codename": "jammy",
                    "id_like": "debian",
                }
            },
        )

    def test_get_os_release_node_returns_none_when_unavailable(self):
        self.assertIsNone(listener.psapi.get_os_release_node({}))

    @patch("listener.psapi.get_os_release_node")
    def test_get_system_node_includes_os_release(self, mock_get_os_release_node):
        mock_get_os_release_node.return_value = listener.nodes.ParentNode(
            "os_release",
            children=[
                listener.nodes.RunnableNode(
                    "pretty_name", method=lambda: ("Test OS", "")
                )
            ],
        )
        system_node = listener.psapi.get_system_node()
        self.assertIn("os_release", system_node.children)

    @patch("listener.psapi.get_os_release_node", return_value=None)
    def test_get_system_node_omits_os_release_when_unavailable(
        self, mock_get_os_release_node
    ):
        system_node = listener.psapi.get_system_node()
        self.assertNotIn("os_release", system_node.children)

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
