import listener.nodes as nodes
import logging
import subprocess
from listener.nodes import ParentNode, RunnableNode, RunnableParentNode, LazyNode
import os.path

def get_smart_data(drive):
    smartctlExists = os.path.isfile("/sbin/smartctl")
    if not smartctlExists:
        return False

    try:
        output = subprocess.check_output("/usr/sbin/smartctl -a " + drive, shell=True, universal_newlines=True).split('\n')
        retcode = 0
    except subprocess.CalledProcessError as e:
        if "Permission denied" in e.output:
                return True

        output = e.output.split('\n');
        retcode = e.returncode
        if retcode == 127:
            return True

    hasSeenFirstAttr = False
    data={}
    for line in output:
        lineItems = line.split()
        dataItem = {}
        if not hasSeenFirstAttr:
            if len(lineItems) > 1 and lineItems[1] == 'ATTRIBUTE_NAME':
                hasSeenFirstAttr = True
            continue

        if len(lineItems) > 0:
            if not lineItems[0].isnumeric():
                break
            dataItem['Name'] = lineItems[1]
            dataItem['Flag'] = lineItems[2]
            dataItem['Value'] = lineItems[3]
            dataItem['Worst'] = lineItems[4]
            dataItem['Threshold'] = lineItems[5]
            dataItem['Type'] = lineItems[6]
            dataItem['Updated'] = lineItems[7]
            dataItem['WhenFailed'] = lineItems[8]
            dataItem['Raw Value'] = lineItems[9]

            data[lineItems[0]] = dataItem

    return data

def get_disk_devices():
    output = subprocess.check_output("ls -l  /dev/disk/by-id/ |  grep -v wwn | grep -v '\-part' | tr -s ' '  | sed 's/\.\.\///g'", shell=True, universal_newlines=True).split('\n')
    devices={}
    for line in output:
        lineItems = line.split();
        itemcount = len(lineItems)
        if itemcount > 2:
            physdev = lineItems[itemcount - 1]
            devid = lineItems[itemcount - 3]
            devices[physdev] = devid

    return devices

def get_disk_node(physdev, devid):
    return RunnableNode(devid, method=lambda:(physdev, ""))

def make_attribute_data_node(name, value):
    return RunnableNode(name, method=lambda:(value, ""))

def make_attribute_node(id, attribute_data):
    attributes = []

    for attribute in attribute_data:
        attributes.append(make_attribute_data_node(attribute, attribute_data[attribute]))

    return ParentNode(id, children=attributes)

def make_disk_node(physdev, devid):
    children = []

    children.append(RunnableNode("devid", method=lambda: (devid, "")))

    data = get_smart_data("/dev/disk/by-id/" + physdev)
    if (data == False):
        return False
    if (data == True):
        return True
    for attribute in data:
        children.append(make_attribute_node(attribute, data[attribute]))

    return ParentNode(physdev, children=children)

def get_disk_info_node():
    disks = get_disk_devices()

    nodes = []
    for disk in disks:
        node = make_disk_node(disks[disk], disk)
        if node == False:
            return ParentNode("Smartctl must be installed", [])
        if node == True:
            return ParentNode("Smartctl must be runnable as the Nagios user and setuid root", [])
        nodes.append(node)

    return ParentNode("disk", children=nodes)

def get_smartmon_disks_node():
    diskdevs = get_disk_devices()

    disks = []
    for  physdev in diskdevs:
        disks.append(get_disk_node(physdev, diskdevs[physdev]))

    return ParentNode("disks", children=disks)

def get_node():
    disks_node = get_smartmon_disks_node()
    disk_node = get_disk_info_node()

    return ParentNode("smartmon", children=[disks_node, disk_node])
