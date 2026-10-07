# tests/test_serial_io.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import threading
import time

import pytest
import serial

from serial_simulator import create_serial_pair
from serial_reader import read_lines


# - **`t.join()`**：主线程等 writer 线程干完活再往下走，防止测试跑完了后台线程还没结束。
# - **`ser.close()`**：用完串口必须关，否则系统资源被占用、设备被锁，别的程序用不了。
#
# 一句话：**join 管"等线程下班"，close 管"还串口钥匙"。**
#
# 这里用 serial_simulator.create_serial_pair() 拿设备名，而不是自己再抄一遍
# pty.openpty() —— 测试要测的是 src/ 里的被测代码，不是测试自己重写的副本。
@pytest.fixture
def virtual_serial():
    """复用被测代码创建虚拟串口对，测试结束自动关闭 master fd"""
    master_fd, slave_name = create_serial_pair()
    yield master_fd, slave_name
    os.close(master_fd)


def _write_later(master_fd, payload, delay=0.2):
    """延迟写入，模拟设备不会在 open 的瞬间就有数据"""
    def writer():
        time.sleep(delay)
        os.write(master_fd, payload)

    t = threading.Thread(target=writer)
    t.start()
    return t


# ========== 场景1：正常读取单行（直接用 pyserial） ==========

def test_serial_receive(virtual_serial):
    master_fd, slave_name = virtual_serial
    t = _write_later(master_fd, b"$GPGGA,123519,4807.038,N\r\n")

    ser = serial.Serial(slave_name, baudrate=9600, timeout=2)
    line = ser.readline()
    ser.close()
    t.join()

    assert line.startswith(b"$GPGGA")


# ========== 场景2：被测函数 read_lines 读多行 ==========

def test_read_lines_multiple(virtual_serial):
    """分三次写入，验证 read_lines 能按 count 读到多行"""
    master_fd, slave_name = virtual_serial

    def writer():
        time.sleep(0.2)
        os.write(master_fd, b"$GPGGA,123519,4807.038,N\r\n")
        time.sleep(0.2)
        os.write(master_fd, b"$GPGGA,123520,4807.039,N\r\n")
        time.sleep(0.2)
        os.write(master_fd, b"$GPGGA,123521,4807.040,N\r\n")

    t = threading.Thread(target=writer)
    t.start()

    lines = read_lines(slave_name, baudrate=9600, count=3, timeout=2)
    t.join()

    assert len(lines) == 3
    assert lines[0].startswith("$GPGGA")
    # read_lines 内部 decode + strip，不该残留 \r
    assert all('\r' not in line for line in lines)


def test_read_lines_single(virtual_serial):
    """只写一行但 count=3：应返回 1 行，超时部分不计入"""
    master_fd, slave_name = virtual_serial
    t = _write_later(master_fd, b"$GPGGA,123519,4807.038,N\r\n")

    lines = read_lines(slave_name, baudrate=9600, count=3, timeout=1)
    t.join()

    assert len(lines) == 1
    assert lines[0] == "$GPGGA,123519,4807.038,N"


# ========== 场景3：超时（不写任何数据） ==========

def test_read_lines_timeout_returns_empty(virtual_serial):
    """没有数据时 readline 返回 b''，read_lines 里 if line 会跳过，最终返回空列表"""
    _, slave_name = virtual_serial

    lines = read_lines(slave_name, baudrate=9600, count=3, timeout=1)

    assert lines == []


def test_read_lines_count_zero(virtual_serial):
    """边界：count=0 时一次都不该读，直接返回空列表"""
    _, slave_name = virtual_serial

    lines = read_lines(slave_name, baudrate=9600, count=0, timeout=1)

    assert lines == []


# ========== 场景4：格式错（非 ASCII 字节被忽略，不崩溃） ==========

def test_read_lines_non_ascii_ignored(virtual_serial):
    """read_lines 用 errors='ignore' 解码，非法字节应被丢弃而不是抛异常"""
    master_fd, slave_name = virtual_serial
    t = _write_later(master_fd, b"$GPGGA,\xff\xfe,123519\r\n")

    lines = read_lines(slave_name, baudrate=9600, count=1, timeout=2)
    t.join()

    assert len(lines) == 1
    assert lines[0].startswith("$GPGGA")


# ========== 串口模拟器自身 ==========

def test_create_serial_pair():
    """create_serial_pair 应返回可用的 fd 和设备名"""
    master_fd, slave_name = create_serial_pair()
    try:
        assert isinstance(master_fd, int)
        assert slave_name.startswith('/dev/')
        assert os.path.exists(slave_name)
    finally:
        os.close(master_fd)