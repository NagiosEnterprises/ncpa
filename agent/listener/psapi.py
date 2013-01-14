import psutil as ps
import os
import logging

class Node(object):
    
    def __init__(self, name, method=None, children=[], *args, **kwargs):
        if method == None:
            self.method = self.walk
        else:
            self.method = method
        self.children = children
        self.name = name
    
    def accessor(self, path):
        logging.warning(path)
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
            stat[child.name] = child.run()
        return stat
    
    def run(self):
        return {self.name : self.method()}
        

def convert_ps_disk_val(named_tuple):
    stat = {}
    order_list = ['read_count', 'write_count', 'read_bytes', 'write_bytes', 'read_time', 'write_time']
    for device in named_tuple:
        stat[device] = {}
        for metric in order_list:
            stat[device][metric] = getattr(device, order_list)

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

disk_read_count = Node('read_count', method=lambda: ps.disk_io_counters(perdisk=True))
disk_write_count = Node('write_count', method=lambda: ps.disk_io_counters(perdisk=True))
disk_read_bytes = Node('read_bytes', method=lambda: ps.disk_io_counters(perdisk=True))
disk_write_bytes = Node('write_bytes', method=lambda: ps.disk_io_counters(perdisk=True))
disk_read_time = Node('read_time', method=lambda: ps.disk_io_counters(perdisk=True))
disk_write_time = Node('write_time', method=lambda: dict(ps.disk_io_counters(perdisk=True)))

disk = Node('disk', children=(disk_read_count, disk_write_count, disk_read_bytes, disk_write_bytes, disk_read_time, disk_write_time))

plugins = Node('plugins', method=lambda: [x for x in os.listdir('plugins') if os.path.isfile('plugins/%s' % x)] + ['check_memory', 'check_swap', 'check_cpu'])

agent = Node('agent', children=(plugins,))

root = Node('root', children=(cpu, memory, disk, agent))
