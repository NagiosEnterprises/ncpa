import psutil as ps
import os
import logging
import datetime
import time
import re
import platform
import server
from nodes import ParentNode, RunnableNode, RunnableParentNode, LazyNode
from pluginnodes import PluginAgentNode
import services
import processes
import environment

importables = (
    'windowscounters',
    'windowslogs'
)

def get_uptime():
    current_time = time.time()
    epoch_boot = int(current_time)
    return (epoch_boot - ps.boot_time(), 's')

def make_disk_nodes(disk_name):
    read_time = RunnableNode('read_time', method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].read_time, 'ms'))
    write_time = RunnableNode('write_time',
                              method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].write_time, 'ms'))
    read_count = RunnableNode('read_count',
                              method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].read_count, 'c'))
    write_count = RunnableNode('write_count',
                               method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].write_count, 'c'))
    read_bytes = RunnableNode('read_bytes',
                              method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].read_bytes, 'B'))
    write_bytes = RunnableNode('write_bytes',
                               method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].write_bytes, 'B'))
    return ParentNode(disk_name, children=[read_time, write_time, read_count, write_count, read_bytes, write_bytes])


def make_mountpoint_nodes(partition_name):
    mountpoint = partition_name.mountpoint

    total_size = RunnableNode('total_size', method=lambda: (ps.disk_usage(mountpoint).total, 'B'))
    used = RunnableNode('used', method=lambda: (ps.disk_usage(mountpoint).used, 'B'))
    free = RunnableNode('free', method=lambda: (ps.disk_usage(mountpoint).free, 'B'))
    used_percent = RunnableNode('used_percent', method=lambda: (ps.disk_usage(mountpoint).percent, '%'))
    device_name = RunnableNode('device_name', method=lambda: ([partition_name.device], ''))
    fstype = RunnableNode('fstype', method=lambda: (partition_name.fstype, ''))
    opts = RunnableNode('opts', method=lambda: (partition_name.opts, ''))
    safe_mountpoint = re.sub(r'[\\/]+', '|', mountpoint)

    node_children = [total_size, used, free, used_percent, device_name, fstype, opts]

    # Unix specific inode counter ~ sorry Windows! :'(
    if environment.SYSTEM != 'Windows':
        st = os.statvfs(mountpoint)
        iu = st.f_files - st.f_ffree
        inodes = RunnableNode('inodes', method=lambda: (st.f_files, 'inodes'))
        inodes_used = RunnableNode('inodes_used', method=lambda: (iu, 'inodes'))
        inodes_free = RunnableNode('inodes_free', method=lambda: (st.f_ffree, 'inodes'))
        node_children.append(inodes)
        node_children.append(inodes_used)
        node_children.append(inodes_free)

    # Make and return the full parent node
    return RunnableParentNode(safe_mountpoint,
                              children=node_children,
                              primary='used_percent',
                              custom_output='Used disk space was',
                              include=('total_size', 'used', 'free', 'used_percent'))

def make_mount_other_nodes(partition):
    dvn = RunnableNode('device_name', method=lambda: ([partition.device], ''))
    fstype = RunnableNode('fstype', method=lambda: (partition.fstype, ''))
    opts = RunnableNode('opts', method=lambda: (partition.opts, ''))
    safe_mountpoint = re.sub(r'[\\/]+', '|', partition.mountpoint)
    return ParentNode(safe_mountpoint, children=[dvn, fstype, opts])

def make_if_nodes(if_name):
    bytes_sent = RunnableNode('bytes_sent', method=lambda: (ps.net_io_counters(pernic=True)[if_name].bytes_sent, 'B'))
    bytes_recv = RunnableNode('bytes_recv', method=lambda: (ps.net_io_counters(pernic=True)[if_name].bytes_recv, 'B'))
    packets_sent = RunnableNode('packets_sent',
                                method=lambda: (ps.net_io_counters(pernic=True)[if_name].packets_sent, 'packets'))
    packets_recv = RunnableNode('packets_recv',
                                method=lambda: (ps.net_io_counters(pernic=True)[if_name].packets_recv, 'packets'))
    errin = RunnableNode('errin', method=lambda: (ps.net_io_counters(pernic=True)[if_name].errin, 'errors'))
    errout = RunnableNode('errout', method=lambda: (ps.net_io_counters(pernic=True)[if_name].errout, 'errors'))
    dropin = RunnableNode('dropin', method=lambda: (ps.net_io_counters(pernic=True)[if_name].dropin, 'packets'))
    dropout = RunnableNode('dropout', method=lambda: (ps.net_io_counters(pernic=True)[if_name].dropout, 'packets'))
    return ParentNode(if_name, children=[bytes_sent, bytes_recv, packets_sent,
                      packets_recv, errin, errout, dropin, dropout])


def get_timezone():
    return time.tzname, ''


def get_system_node():
    sys_system = RunnableNode('system', method=lambda: (platform.uname()[0], ''))
    sys_node = RunnableNode('node', method=lambda: (platform.uname()[1], ''))
    sys_release = RunnableNode('release', method=lambda: (platform.uname()[2], ''))
    sys_version = RunnableNode('version', method=lambda: (platform.uname()[3], ''))
    sys_machine = RunnableNode('machine', method=lambda: (platform.uname()[4], ''))
    sys_processor = RunnableNode('processor', method=lambda: (platform.uname()[5], ''))
    sys_uptime = RunnableNode('uptime', method=get_uptime)
    sys_agent = RunnableNode('agent_version', method=lambda: (server.__VERSION__, ''))
    sys_time = RunnableNode('time', method=lambda: (time.time(), ''))
    sys_timezone = RunnableNode('timezone', method=get_timezone)
    return ParentNode('system', children=[sys_system, sys_node, sys_release, sys_version,
                      sys_machine, sys_processor, sys_uptime, sys_agent, sys_timezone, sys_time])


def get_cpu_node():
    cpu_count = RunnableNode('count', method=lambda: ([len(ps.cpu_percent(percpu=True))], 'cores'))
    cpu_percent = LazyNode('percent', method=lambda: (ps.cpu_percent(interval=1, percpu=True), '%'))
    cpu_user = RunnableNode('user', method=lambda: ([x.user for x in ps.cpu_times(percpu=True)], 'ms'))
    cpu_system = RunnableNode('system', method=lambda: ([x.system for x in ps.cpu_times(percpu=True)], 'ms'))
    cpu_idle = RunnableNode('idle', method=lambda: ([x.idle for x in ps.cpu_times(percpu=True)], 'ms'))
    return ParentNode('cpu', children=[cpu_count, cpu_system, cpu_percent, cpu_user, cpu_idle])


def get_memory_node():
    mem_virt_total = RunnableNode('total', method=lambda: (ps.virtual_memory().total, 'B'))
    mem_virt_available = RunnableNode('available', method=lambda: (ps.virtual_memory().available, 'B'))
    mem_virt_percent = RunnableNode('percent', method=lambda: (ps.virtual_memory().percent, '%'))
    mem_virt_used = RunnableNode('used', method=lambda: (ps.virtual_memory().used, 'B'))
    mem_virt_free = RunnableNode('free', method=lambda: (ps.virtual_memory().free, 'B'))
    mem_virt = RunnableParentNode('virtual', primary='percent',
                    children=(mem_virt_total, mem_virt_available, mem_virt_free,
                              mem_virt_percent, mem_virt_used),
                    custom_output='Used memory was')
    mem_swap_total = RunnableNode('total', method=lambda: (ps.swap_memory().total, 'B'))
    mem_swap_percent = RunnableNode('percent', method=lambda: (ps.swap_memory().percent, '%'))
    mem_swap_used = RunnableNode('used', method=lambda: (ps.swap_memory().used, 'B'))
    mem_swap_free = RunnableNode('free', method=lambda: (ps.swap_memory().free, 'B'))
    mem_swap = RunnableParentNode('swap', primary='percent',
                    children=[mem_swap_total, mem_swap_free, mem_swap_percent, mem_swap_used],
                    custom_output='Used swap was')
    return ParentNode('memory', children=[mem_virt, mem_swap])


def get_disk_node():
    disk_counters = [make_disk_nodes(x) for x in list(ps.disk_io_counters(perdisk=True).keys())]

    disk_mountpoints = []
    disk_parts = []
    for x in ps.disk_partitions(all=True):
        if os.path.isdir(x.mountpoint):
            tmp = make_mountpoint_nodes(x)
            disk_mountpoints.append(tmp)
        else:
            tmp = make_mount_other_nodes(x)
            disk_parts.append(tmp)

    disk_logical = ParentNode('logical', children=disk_mountpoints)
    disk_physical = ParentNode('physical', children=disk_counters)
    disk_mount = ParentNode('mount', children=disk_parts)

    return ParentNode('disk', children=[disk_physical, disk_logical, disk_mount])


def get_interface_node():
    if_children = [make_if_nodes(x) for x in list(ps.net_io_counters(pernic=True).keys())]
    return ParentNode('interface', children=if_children)


def get_plugins_node():
    return PluginAgentNode('plugins')


def get_user_node():
    user_count = RunnableNode('count', method=lambda: (len([x.name for x in ps.users()]), 'users'))
    user_list = RunnableNode('list', method=lambda: ([x.name for x in ps.users()], 'users'))
    return ParentNode('user', children=[user_count, user_list])


def get_root_node():
    cpu = get_cpu_node()
    memory = get_memory_node()
    disk = get_disk_node()
    interface = get_interface_node()
    plugins = get_plugins_node()
    user = get_user_node()
    system = get_system_node()
    service = services.get_node()
    process = processes.get_node()

    children = [cpu, memory, disk, interface, plugins, user, system, service, process]

    if environment.SYSTEM == "Windows":
        for importable in importables:
            try:
                relative_name = 'listener.' + importable
                tmp = __import__(relative_name, fromlist=['get_node'])
                get_node = getattr(tmp, 'get_node')

                node = get_node()
                children.append(node)
                logging.debug("Imported %s into the API tree.", importable)
            except ImportError:
                logging.warning("Could not import %s, skipping.", importable)
            except AttributeError:
                logging.warning("Trying to import %s but does not get_node() function, skipping.", importable)

    return ParentNode('root', children=children)


# The root node (cached objects)
root = get_root_node()


def refresh():
    global root
    root = get_root_node()
    return True


def getter(accessor, config, full_path, cache=False):
    global root

    # Sanity check. If accessor is None, we can do nothing meaningfully, and we need to stop.
    if accessor is None:
        return
    path = [re.sub('%2f', '/', x, flags=re.I) for x in accessor.split('/') if x]
    if len(path) > 0 and path[0] == 'api':
        path = path[1:]

    # Check if this should be a cached query or if we should reset the root
    # node. This normally only happens on new API calls. When we are using
    # websockets we use the cached version while it makes requests.
    if not cache:
        root = get_root_node()

    root.reset_valid_nodes()
    return root.accessor(path, config, full_path)
