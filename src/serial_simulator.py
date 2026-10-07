# src/serial_simulator.py
import os
import pty

def create_serial_pair():
    """创建一对虚拟串口，返回 (master_fd, slave_name)"""
    master_fd, slave_fd = pty.openpty()#创建一对主从设备
    slave_name = os.ttyname(slave_fd)#获取从设备的设备文件名
    return master_fd, slave_name
