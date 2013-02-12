import psutil as ps
import os
import logging
import inspect
import re

this_path = inspect.currentframe().f_code.co_filename
this_dir  = os.path.dirname(this_path)
plugins   = os.path.abspath("%s/../plugins" % this_dir)

class Node(object):
    
    def __init__(self, name, method=None, children=[], *args, **kwargs):
        if method == None:
            self.method = self.walk
        else:
            self.method = method
        self.children = children
        self.name = name
    
    def accessor(self, path):
        if path:
            for x in self.children:
                if x.name == path[0]:
                    return x.accessor(path[1:])
            raise IndexError('No node with that name: %s' % path[0])
        else:
            return self.run()
    
    def walk(self):
        stat = {}
        for child in self.children:
            stat.update(child.run())
        return stat
    
    def run(self):
        return {self.name : self.method()}

def make_disk_nodes(disk_name):
    read_time = Node('read_time', method=lambda: ps.disk_io_counters(perdisk=True)[disk_name].read_time)
    write_time = Node('write_time', method=lambda: ps.disk_io_counters(perdisk=True)[disk_name].write_time)
    read_count = Node('read_count', method=lambda: ps.disk_io_counters(perdisk=True)[disk_name].read_count)
    write_count = Node('write_count', method=lambda: ps.disk_io_counters(perdisk=True)[disk_name].write_count)
    read_bytes = Node('read_bytes', method=lambda: ps.disk_io_counters(perdisk=True)[disk_name].read_bytes)
    write_bytes = Node('write_bytes', method=lambda: ps.disk_io_counters(perdisk=True)[disk_name].write_bytes)
    return Node(disk_name, children=(read_time, write_time, read_count, write_count, read_bytes, write_bytes))

def make_mountpoint_nodes(partition_name):
    mountpoint = partition_name.mountpoint
    total_size = Node('total_size', method=lambda: ps.disk_usage(mountpoint).total)
    used = Node('used', method=lambda: ps.disk_usage(mountpoint).used)
    free = Node('free', method=lambda: ps.disk_usage(mountpoint).free)
    used_percent = Node('used_percent', method=lambda: ps.disk_usage(mountpoint).percent)
    device_name = Node('device_name', method=lambda: partition_name.device)
    safe_mountpoint = re.sub(r'[\\/]+', '|', mountpoint)
    return Node(safe_mountpoint, children=(total_size, used, free, used_percent, device_name))
    
def make_if_nodes(if_name):
    bytes_sent = Node('bytes_sent', method=lambda: ps.network_io_counters(pernic=True)[if_name].bytes_sent)
    bytes_recv = Node('bytes_recv', method=lambda: ps.network_io_counters(pernic=True)[if_name].bytes_recv)
    packets_sent = Node('packets_sent', method=lambda: ps.network_io_counters(pernic=True)[if_name].packets_sent)
    packets_recv = Node('packets_recv', method=lambda: ps.network_io_counters(pernic=True)[if_name].packets_recv)
    errin = Node('errin', method=lambda: ps.network_io_counters(pernic=True)[if_name].errin)
    errout = Node('errout', method=lambda: ps.network_io_counters(pernic=True)[if_name].errout)
    dropin = Node('dropin', method=lambda: ps.network_io_counters(pernic=True)[if_name].dropin)
    dropout = Node('dropout', method=lambda: ps.network_io_counters(pernic=True)[if_name].dropout)
    return Node(if_name, children=(bytes_sent, bytes_recv, packets_sent, packets_recv, errin, errout, dropin, dropout))

#~ CPU Tree
cpu_count = Node('count', method=lambda: len(ps.cpu_percent(percpu=True)))
cpu_percent = Node('percentage', method=lambda: ps.cpu_percent(1, percpu=True))
cpu_user = Node('user', method=lambda: [x.user for x in ps.cpu_times(percpu=True)])
cpu_system = Node('system', method=lambda: [x.system for x in ps.cpu_times(percpu=True)])
cpu_idle = Node('idle', method=lambda: [x.idle for x in ps.cpu_times(percpu=True)])

cpu = Node('cpu', children=(cpu_count, cpu_system, cpu_percent, cpu_user, cpu_idle))

#~ Memory Tree
mem_virt_total = Node('total', method=lambda: ps.virtual_memory().total)
mem_virt_available = Node('available', method=lambda: ps.virtual_memory().available)
mem_virt_percent = Node('percent', method=lambda: ps.virtual_memory().percent)
mem_virt_used = Node('used', method=lambda: ps.virtual_memory().used)
mem_virt_free = Node('free', method=lambda: ps.virtual_memory().free)

mem_virt = Node('virtual', children=(mem_virt_total, mem_virt_available, mem_virt_free, mem_virt_percent, mem_virt_used))

mem_swap_total = Node('total', method=lambda: ps.swap_memory().total)
mem_swap_percent = Node('percent', method=lambda: ps.swap_memory().percent)
mem_swap_used = Node('used', method=lambda: ps.swap_memory().used)
mem_swap_free = Node('free', method=lambda: ps.swap_memory().free)

mem_swap = Node('swap', children=(mem_swap_total, mem_swap_free, mem_swap_percent, mem_swap_used))

memory = Node('memory', children=(mem_virt, mem_swap))

disk_counters = [make_disk_nodes(x) for x in ps.disk_io_counters(perdisk=True).keys()]

disk_mountpoints = []
for x in ps.disk_partitions():
    if os.path.isdir(x.mountpoint):
        tmp = make_mountpoint_nodes(x)
        disk_mountpoints.append(tmp)

disk_logical = Node('logical', children=disk_mountpoints)
disk_physical = Node('phyical', children=disk_counters)

disk = Node('disk', children=(disk_physical, disk_logical))

if_children = [make_if_nodes(x) for x in ps.network_io_counters(pernic=True).keys()]

interface = Node('interface', children=if_children)

plugin = Node('plugin', method=lambda: [os.path.basename(x) for x in os.listdir(plugins) if os.path.isfile(os.path.normpath('%s/%s') % (plugins, x))])

agent = Node('agent', children=(plugin,))

user_count = Node('count', method=lambda: len([x.name for x in ps.get_users()]))
user_list  = Node('list', method=lambda: [x.name for x in ps.get_users()])

user = Node('user', children=(user_count, user_list))

root = Node('root', children=(cpu, memory, disk, interface, agent, user))

def getter(accessor=''):
    path = [x for x in accessor.split('/') if x]
    logging.info(path)
    return root.accessor(path)
