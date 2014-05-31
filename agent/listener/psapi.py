import psutil as ps
import os
import logging
import re
import platform

from nodes import ParentNode, RunnableNode, LazyNode
from pluginnodes import PluginAgentNode
root = None


#
#class ProcessNode(LazyNode):
#
#    def __init__(self, *args, **kwargs):
#        super(ProcessNode, self).__init__(*args, **kwargs)
#
#    def parse_query(self, path, *args, **kwargs):
#        desired_proc = path[0].replace('|', '/')
#        metrics = {'count': 0}
#        for proc in ps.process_iter():
#            if proc.name == desired_proc:
#                metrics['count'] += 1
#        try:
#            if path[1] == 'count':
#                return {'count': metrics['count']}
#        except IndexError:
#            return {desired_proc: metrics}
#
#
#class ServiceNode(LazyNode):
#
#    def __init__(self, *args, **kwargs):
#        super(ServiceNode, self).__init__(*args, **kwargs)
#
#    def run(self, path, *args, **kwargs):
#        if path:
#            return self.parse_query(path)
#        else:
#            try:
#                return {self.name: psextensions.get_services()}
#            except Exception, e:
#                return {self.name: 'Error getting services: %s' % unicode(e)}
#
#    def parse_query(self, path, *args, **kwargs):
#        desired_service = path[0].replace('|', '/')
#
#        try:
#            desired_state = path[1]
#        except IndexError:
#            desired_state = None
#
#        services = psextensions.get_services()
#
#        if desired_state:
#            return {desired_service: services.get(desired_service, 'Service not found') == desired_state}
#        else:
#            return {desired_service: services.get(desired_service, 'Service not found')}
def make_disk_nodes(disk_name):
    read_time = RunnableNode('read_time', method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].read_time, 'ms'))
    write_time = RunnableNode('write_time', method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].write_time, 'ms'))
    read_count = RunnableNode('read_count', method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].read_count, 'c'))
    write_count = RunnableNode('write_count', method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].write_count, 'c'))
    read_bytes = RunnableNode('read_bytes', method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].read_bytes, 'b'))
    write_bytes = RunnableNode('write_bytes', method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].write_bytes, 'b'))
    return ParentNode(disk_name, children=[read_time, write_time, read_count, write_count, read_bytes, write_bytes])


def make_mountpoint_nodes(partition_name):
    mountpoint = partition_name.mountpoint
    total_size = RunnableNode('total_size', method=lambda: (ps.disk_usage(mountpoint).total, 'b'))
    used = RunnableNode('used', method=lambda: (ps.disk_usage(mountpoint).used, 'b'))
    free = RunnableNode('free', method=lambda: (ps.disk_usage(mountpoint).free, 'b'))
    used_percent = RunnableNode('used_percent', method=lambda: (ps.disk_usage(mountpoint).percent, '%'))
    device_name = RunnableNode('device_name', method=lambda: partition_name.device)
    safe_mountpoint = re.sub(r'[\\/]+', '|', mountpoint)
    return ParentNode(safe_mountpoint, children=[total_size, used, free, used_percent, device_name])


def make_if_nodes(if_name):
    bytes_sent = RunnableNode('bytes_sent', method=lambda: (ps.net_io_counters(pernic=True)[if_name].bytes_sent, 'b'))
    bytes_recv = RunnableNode('bytes_recv', method=lambda: (ps.net_io_counters(pernic=True)[if_name].bytes_recv, 'b'))
    packets_sent = RunnableNode('packets_sent', method=lambda: (ps.net_io_counters(pernic=True)[if_name].packets_sent, 'c'))
    packets_recv = RunnableNode('packets_recv', method=lambda: (ps.net_io_counters(pernic=True)[if_name].packets_recv, 'c'))
    errin = RunnableNode('errin', method=lambda: (ps.net_io_counters(pernic=True)[if_name].errin, 'c'))
    errout = RunnableNode('errout', method=lambda: (ps.net_io_counters(pernic=True)[if_name].errout, 'c'))
    dropin = RunnableNode('dropin', method=lambda: (ps.net_io_counters(pernic=True)[if_name].dropin, 'c'))
    dropout = RunnableNode('dropout', method=lambda: (ps.net_io_counters(pernic=True)[if_name].dropout, 'c'))
    return ParentNode(if_name, children=[bytes_sent, bytes_recv, packets_sent, packets_recv, errin, errout, dropin, dropout])


def get_system_node():
    sys_system = RunnableNode('system', method=lambda: platform.uname()[0])
    sys_node = RunnableNode('node', method=lambda: platform.uname()[1])
    sys_release = RunnableNode('release', method=lambda: platform.uname()[2])
    sys_version = RunnableNode('version', method=lambda: platform.uname()[3])
    sys_machine = RunnableNode('machine', method=lambda: platform.uname()[4])
    sys_processor = RunnableNode('processor', method=lambda: platform.uname()[5])
    return ParentNode('system', children=[sys_system, sys_node, sys_release, sys_version, sys_machine, sys_processor])


def get_cpu_node():
    cpu_count = RunnableNode('count', method=lambda: len(ps.cpu_percent(percpu=True)))
    cpu_percent = LazyNode('percent', method=lambda: (ps.cpu_percent(interval=1, percpu=True), '%'))
    cpu_user = RunnableNode('user', method=lambda: ([x.user for x in ps.cpu_times(percpu=True)], 'ms'))
    cpu_system = RunnableNode('system', method=lambda: ([x.system for x in ps.cpu_times(percpu=True)], 'ms'))
    cpu_idle = RunnableNode('idle', method=lambda: ([x.idle for x in ps.cpu_times(percpu=True)], 'ms'))
    return ParentNode('cpu', children=[cpu_count, cpu_system, cpu_percent, cpu_user, cpu_idle])


def get_memory_node():
    mem_virt_total = RunnableNode('total', method=lambda: (ps.virtual_memory().total, 'b'))
    mem_virt_available = RunnableNode('available', method=lambda: (ps.virtual_memory().available, 'b'))
    mem_virt_percent = RunnableNode('percent', method=lambda: (ps.virtual_memory().percent, '%'))
    mem_virt_used = RunnableNode('used', method=lambda: (ps.virtual_memory().used, 'b'))
    mem_virt_free = RunnableNode('free', method=lambda: (ps.virtual_memory().free, 'b'))
    mem_virt = ParentNode('virtual', children=(mem_virt_total, mem_virt_available, mem_virt_free, mem_virt_percent, mem_virt_used))
    mem_swap_total = RunnableNode('total', method=lambda: (ps.swap_memory().total, 'b'))
    mem_swap_percent = RunnableNode('percent', method=lambda: (ps.swap_memory().percent, '%'))
    mem_swap_used = RunnableNode('used', method=lambda: (ps.swap_memory().used, 'b'))
    mem_swap_free = RunnableNode('free', method=lambda: (ps.swap_memory().free, 'b'))
    mem_swap = ParentNode('swap', children=[mem_swap_total, mem_swap_free, mem_swap_percent, mem_swap_used])
    return ParentNode('memory', children=[mem_virt, mem_swap])


def get_disk_node():
    disk_counters = [make_disk_nodes(x) for x in list(ps.disk_io_counters(perdisk=True).keys())]

    disk_mountpoints = []
    for x in ps.disk_partitions():
        if os.path.isdir(x.mountpoint):
            tmp = make_mountpoint_nodes(x)
            disk_mountpoints.append(tmp)

    disk_logical = ParentNode('logical', children=disk_mountpoints)
    disk_physical = ParentNode('physical', children=disk_counters)

    return ParentNode('disk', children=[disk_physical, disk_logical])


def get_interface_node():
    if_children = [make_if_nodes(x) for x in list(ps.net_io_counters(pernic=True).keys())]
    return ParentNode('interface', children=if_children)


def get_agent_node():
    plugin = PluginAgentNode('plugin')
    return ParentNode('agent', children=(plugin,))


def get_user_node():
    user_count = RunnableNode('count', method=lambda: (len([x.name for x in ps.get_users()]), 'c'))
    user_list = RunnableNode('list', method=lambda: [x.name for x in ps.get_users()])
    return ParentNode('user', children=[user_count, user_list])


def get_process_node():
    return ProcessNode('process')


def get_service_node():
    return ServiceNode('service')


def get_root_node(*args):
    cpu = get_cpu_node()
    memory = get_memory_node()
    disk = get_disk_node()
    interface = get_interface_node()
    agent = get_agent_node()
    user = get_user_node()
    #process = get_process_node()
    #service = get_service_node()
    system = get_system_node()
    return ParentNode('root', children=[cpu, memory, disk, interface, agent, user, system])


def init_root(*args):
    global root
    root = get_root_node()
    for n in args:
        root.add_child(n)


def getter(accessor, config):
    logging.debug('Getting accessor: %s', accessor)
    path = [x for x in accessor.split('/') if x]
    if len(path) > 0 and path[0] == 'api':
        path = path[1:]
    return root.accessor(path, config)
