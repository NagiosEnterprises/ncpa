import psutil

def check_cpu(item):
    item.values = psutil.cpu_percent(percpu=True)
    item.unit = '%'
    item.nice = 'CPU_Load'
    item.set_stdout('CPU Utilization is at')
    return item

def check_swap(item):
    item.unit = '%'
    item.nice = 'Swap_Usage'
    item.set_values(psutil.swap_memory().percent)
    item.set_stdout('Swap Usage is at')
    return item

def check_memory(item):
    item.unit = '%'
    item.nice = 'Memory_Usage'
    item.set_values(psutil.virtual_memory().percent)
    item.set_stdout('Physical Memory Usage is at')
    return item
    
    
