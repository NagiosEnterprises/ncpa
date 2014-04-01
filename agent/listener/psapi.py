import psutil as ps
import os
import logging
import re
import platform
import sys
import psextensions

plugins   = u''

class Node(object):

    def __init__(self, name, method=None, children=[], *args, **kwargs):
        if method == None:
            self.method = self.walk
        else:
            self.method = method
        self.children = children
        self.name = name
        self.lazy = False

    def accessor(self, path, *args, **kwargs):
        if path:
            for x in self.children:
                if x.name == path[0]:
                    return x.accessor(path=path[1:], *args, **kwargs)
            raise IndexError(u'No node with that name: %s' % path[0])
        else:
            kwargs[u'path'] = path[:1]
            return self.run(*args, **kwargs)

    def walk(self, *args, **kwargs):
        stat = {}
        for child in self.children:
            stat.update(child.run(walk=True, *args, **kwargs))
        return stat

    def run(self, walk=False, *args, **kwargs):
        if walk and self.lazy:
            return {self.name: u'lazy'}
        try:
            retval = self.method(*args, **kwargs)
        except TypeError:
            retval = self.method()
        return {self.name : retval}

class LazyNode(Node):

    def __init__(self, *args, **kwargs):
        super(LazyNode, self).__init__(*args, **kwargs)

    def accessor(self, path, *args, **kwargs):
        return self.run(path, *args, **kwargs)

    def run(self, path, *args, **kwargs):
        if path:
            return self.parse_query(path)
        else:
            return {self.name : []}

class ProcessNode(LazyNode):

    def __init__(self, *args, **kwargs):
        super(ProcessNode, self).__init__(*args, **kwargs)

    def parse_query(self, path):
        desired_proc = path[0].replace(u'|', u'/')
        metrics = {u'count' : 0 }
        count = 0
        for proc in ps.process_iter():
            if proc.name == desired_proc:
                metrics[u'count'] += 1
        try:
            if path[1] == u'count':
                return {u'count' : metrics[u'count']}
        except IndexError:
            return {desired_proc : metrics }

class ServiceNode(LazyNode):

    def __init__(self, *args, **kwargs):
        super(ServiceNode, self).__init__(*args, **kwargs)

    def run(self, path, *args, **kwargs):
        if path:
            return self.parse_query(path)
        else:
            try:
                return {self.name: psextensions.get_services()}
            except Exception, e:
                return {self.name: u'Error getting services: %s' % unicode(e)}

    def parse_query(self, path):
        desired_service = path[0].replace(u'|', u'/')

        try:
            desired_state = path[1]
        except IndexError:
            desired_state = None

        services = psextensions.get_services()

        if desired_state:
            return {desired_service: services.get(desired_service, u'Service not found') == desired_state}
        else:
            return {desired_service: services.get(desired_service, u'Service not found')}

def make_disk_nodes(disk_name):
    read_time = Node(u'read_time', method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].read_time,u'ms'))
    write_time = Node(u'write_time', method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].write_time, u'ms'))
    read_count = Node(u'read_count', method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].read_count, u'c'))
    write_count = Node(u'write_count', method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].write_count, u'c'))
    read_bytes = Node(u'read_bytes', method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].read_bytes, u'b'))
    write_bytes = Node(u'write_bytes', method=lambda: (ps.disk_io_counters(perdisk=True)[disk_name].write_bytes, u'b'))
    return Node(disk_name, children=(read_time, write_time, read_count, write_count, read_bytes, write_bytes))

def make_mountpoint_nodes(partition_name):
    mountpoint = partition_name.mountpoint
    total_size = Node(u'total_size', method=lambda: (ps.disk_usage(mountpoint).total, u'b'))
    used = Node(u'used', method=lambda: (ps.disk_usage(mountpoint).used, u'b'))
    free = Node(u'free', method=lambda: (ps.disk_usage(mountpoint).free, u'b'))
    used_percent = Node(u'used_percent', method=lambda: (ps.disk_usage(mountpoint).percent, u'%'))
    device_name = Node(u'device_name', method=lambda: partition_name.device)
    safe_mountpoint = re.sub(ur'[\\/]+', u'|', mountpoint)
    return Node(safe_mountpoint, children=(total_size, used, free, used_percent, device_name))

def make_if_nodes(if_name):
    bytes_sent = Node(u'bytes_sent', method=lambda: (ps.net_io_counters(pernic=True)[if_name].bytes_sent, u'b'))
    bytes_recv = Node(u'bytes_recv', method=lambda: (ps.net_io_counters(pernic=True)[if_name].bytes_recv, u'b'))
    packets_sent = Node(u'packets_sent', method=lambda: (ps.net_io_counters(pernic=True)[if_name].packets_sent, u'c'))
    packets_recv = Node(u'packets_recv', method=lambda: (ps.net_io_counters(pernic=True)[if_name].packets_recv, u'c'))
    errin = Node(u'errin', method=lambda: (ps.net_io_counters(pernic=True)[if_name].errin, u'c'))
    errout = Node(u'errout', method=lambda: (ps.net_io_counters(pernic=True)[if_name].errout, u'c'))
    dropin = Node(u'dropin', method=lambda: (ps.net_io_counters(pernic=True)[if_name].dropin, u'c'))
    dropout = Node(u'dropout', method=lambda: (ps.net_io_counters(pernic=True)[if_name].dropout, u'c'))
    return Node(if_name, children=(bytes_sent, bytes_recv, packets_sent, packets_recv, errin, errout, dropin, dropout))

#~ Sys Tree
sys_system = Node(u'system', method=lambda: platform.uname()[0])
sys_node = Node(u'node', method=lambda: platform.uname()[1])
sys_release = Node(u'release', method=lambda: platform.uname()[2])
sys_version = Node(u'version', method=lambda: platform.uname()[3])
sys_machine = Node(u'machine', method=lambda: platform.uname()[4])
sys_processor = Node(u'processor', method=lambda: platform.uname()[5])

system = Node(u'system', children=(sys_system, sys_node, sys_release, sys_version, sys_machine, sys_processor))

#~ CPU Tree
cpu_count = Node(u'count', method=lambda: len(ps.cpu_percent(percpu=True)))
cpu_percent = Node(u'percent', method=lambda: (ps.cpu_percent(interval=1, percpu=True), u'%'))
cpu_user = Node(u'user', method=lambda: ([x.user for x in ps.cpu_times(percpu=True)], u'ms'))
cpu_system = Node(u'system', method=lambda: ([x.system for x in ps.cpu_times(percpu=True)], u'ms'))
cpu_idle = Node(u'idle', method=lambda: ([x.idle for x in ps.cpu_times(percpu=True)], u'ms'))
cpu_percent.lazy = True

cpu = Node(u'cpu', children=(cpu_count, cpu_system, cpu_percent, cpu_user, cpu_idle))

#~ Memory Tree
mem_virt_total = Node(u'total', method=lambda: (ps.virtual_memory().total, u'b'))
mem_virt_available = Node(u'available', method=lambda: (ps.virtual_memory().available, u'b'))
mem_virt_percent = Node(u'percent', method=lambda: (ps.virtual_memory().percent, u'%'))
mem_virt_used = Node(u'used', method=lambda: (ps.virtual_memory().used, u'b'))
mem_virt_free = Node(u'free', method=lambda: (ps.virtual_memory().free, u'b'))

mem_virt = Node(u'virtual', children=(mem_virt_total, mem_virt_available, mem_virt_free, mem_virt_percent, mem_virt_used))

mem_swap_total = Node(u'total', method=lambda: (ps.swap_memory().total, u'b'))
mem_swap_percent = Node(u'percent', method=lambda: (ps.swap_memory().percent, u'%'))
mem_swap_used = Node(u'used', method=lambda: (ps.swap_memory().used, u'b'))
mem_swap_free = Node(u'free', method=lambda: (ps.swap_memory().free, u'b'))

mem_swap = Node(u'swap', children=(mem_swap_total, mem_swap_free, mem_swap_percent, mem_swap_used))

memory = Node(u'memory', children=(mem_virt, mem_swap))

disk_counters = [make_disk_nodes(x) for x in list(ps.disk_io_counters(perdisk=True).keys())]

disk_mountpoints = []
for x in ps.disk_partitions():
    if os.path.isdir(x.mountpoint):
        tmp = make_mountpoint_nodes(x)
        disk_mountpoints.append(tmp)

disk_logical = Node(u'logical', children=disk_mountpoints)
disk_physical = Node(u'phyical', children=disk_counters)

disk = Node(u'disk', children=(disk_physical, disk_logical))

if_children = [make_if_nodes(x) for x in list(ps.net_io_counters(pernic=True).keys())]

interface = Node(u'interface', children=if_children)

plugin = Node(u'plugin', method=lambda: [x for x in os.listdir(plugins) if os.path.isfile(os.path.normpath(u'%s/%s') % (plugins, x))])

agent = Node(u'agent', children=(plugin,))

user_count = Node(u'count', method=lambda: (len([x.name for x in ps.get_users()]), u'c'))
user_list  = Node(u'list', method=lambda: [x.name for x in ps.get_users()])

process = ProcessNode(u'process')
service = ServiceNode(u'service')

user = Node(u'user', children=(user_count, user_list))

root = Node(u'root', children=(cpu, memory, disk, interface, agent, user, process, service, system))

def getter(accessor=u'', s_plugins=u''):
    global plugins
    logging.debug(u"Using %s" % s_plugins)
    plugins = s_plugins
    path = [x for x in accessor.split(u'/') if x]
    if len(path) > 0  and path[0] == u'api':
        path = path[1:]
    return root.accessor(path)
