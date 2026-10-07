下面是 Day 2 的笔记，直接复制到 `docs/day2-notes.md`。


# Day 2 - fixture + 串口测试 + NMEA 解析

**日期：** 2026-10-09  
**学习时长：** 7 小时  
**今日目标：** 学会 fixture、pyserial、pty 模拟串口、串口测试四种场景、NMEA 解析、数据融合测试。

---

## 一、今天学了什么

- pytest fixture：前置/后置、共享测试数据
- pyserial：打开串口、读一行、写数据、超时
- pty 模拟串口：Mac 上无真实硬件也能练串口测试
- 串口测试四种场景：正常、超时、格式错、边界
- NMEA 语句解析
- 数据融合测试
- 测试调试：ImportError vs NameError
- 测试反模式：`try/except: pass`

---

## 二、核心概念理解

### 1. fixture
测试的"中央厨房"，数据统一备料，测试函数直接"点菜"。

```python
@pytest.fixture
def radar_data():
    return "45.0,100.5,200"

def test_radar_normal_single(radar_data):
    result = parse_radar(radar_data)
    assert len(result) == 1
```

- `@pytest.fixture` 把函数注册为数据供应站
- 测试函数参数名 = fixture 名，pytest 自动注入
- `yield` 之前是前置，之后是后置
- 到岗后管理串口/socket 资源必用

### 2. yield 版 fixture（资源管理）
```python
@pytest.fixture
def gps_serial():
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    yield ser          # 测试期间用
    ser.close()        # 测试完自动关闭
```

### 3. fixture vs parametrize
| 场景 | 用什么 |
|---|---|
| 多个测试用同一份数据 | fixture |
| 需要打开/关闭资源 | fixture + yield |
| 一组相似测试用不同数据 | parametrize |
| 单个测试用的简单数据 | 直接写在测试里 |

### 4. pyserial 核心
```python
import serial

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
line = ser.readline()       # 读一行，超时返回 b''
ser.write(b'$PMTK000*32\r\n')  # 只能写 bytes
ser.close()
```

| 参数/方法 | 说明 |
|---|---|
| baudrate | 波特率，常见 9600、115200 |
| timeout | 读不到数据等几秒 |
| readline() | 读一行，返回 bytes |
| write(data) | 写数据，必须 bytes |
| in_waiting | 缓冲区还有多少字节 |
| close() | 关闭，释放资源 |

### 5. pty 模拟串口
用软件伪造一对串口，主端写、从端读，模拟真实串口通信。

```python
import os
import pty

master_fd, slave_fd = pty.openpty()
slave_name = os.ttyname(slave_fd)   # 如 /dev/ttys003
```

| 概念 | 说明 |
|---|---|
| master_fd | 主端文件描述符，测试端往这里写 |
| slave_name | 从端设备名，被测代码从这里读 |
| 用途 | Mac 无真实硬件时练串口测试 |
| 到岗后 | slave_name 换成 /dev/ttyUSB0 |

### 6. 串口测试四种场景
| 场景 | 例子 |
|---|---|
| 正常 | `$GPGGA,123519,4807.038,N\r\n` |
| 超时 | 不写数据，readline 返回 b'' |
| 格式错 | 无 `$` 前缀、非 ASCII、字段太少 |
| 边界 | 空字段、超长字段、多字段 |

### 7. NMEA 解析
GPS 等设备输出的文本协议，以 `$` 开头，逗号分隔。

```python
def parse_nmea(raw: bytes) -> dict:
    if not raw:
        raise ValueError("empty")
    try:
        line = raw.decode('ascii').strip()
    except UnicodeDecodeError:
        raise ValueError("non-ascii")
    if not line.startswith('$'):
        raise ValueError("missing $")
    parts = line.split(',')
    if len(parts) < 2:
        raise ValueError("too few fields")
    return {'type': parts[0], 'fields': parts[1:]}
```

四道关：空 → 非 ASCII → 无 `$` → 字段太少。

### 8. b'' 是什么
空的字节串（bytes），长度为 0。

- `''` 是空字符串（str）
- `b''` 是空字节串（bytes）
- 串口 readline 超时返回 `b''`
- `if line` 能拦住它，因为空序列是假

### 9. t.join() 和 ser.close()
| 代码 | 作用 |
|---|---|
| t.join() | 主线程等子线程干完活再往下走 |
| ser.close() | 用完串口必须关，否则资源被锁 |

### 10. pass 是什么
Python 的"什么都不做"占位符。语法上需要写点什么，但逻辑上不想执行操作。

```python
if x > 0:
    pass   # 合法，什么都不做
```

---

## 三、关键代码 / 命令

### 常用命令
```bash
source .venv/bin/activate
pip install pytest pyserial

# 跑测试
pytest tests/test_nmea_parser.py -v

# 只跑某个测试
pytest tests/test_nmea_parser.py::test_normal -v

# 覆盖率
pytest --cov=src --cov-report=term-missing
```

### NMEA 解析器
```python
def parse_nmea(raw: bytes) -> dict:
    if not raw:
        raise ValueError("empty")
    try:
        line = raw.decode('ascii').strip()
    except UnicodeDecodeError:
        raise ValueError("non-ascii")
    if not line.startswith('$'):
        raise ValueError("missing $")
    parts = line.split(',')
    if len(parts) < 2:
        raise ValueError("too few fields")
    return {'type': parts[0], 'fields': parts[1:]}
```

### 串口读多行
```python
import serial

def read_lines(port, baudrate=9600, count=3, timeout=2):
    ser = serial.Serial(port, baudrate, timeout=timeout)
    lines = []
    try:
        for _ in range(count):
            line = ser.readline()
            if line:
                lines.append(line.decode('ascii', errors='ignore').strip())
    finally:
        ser.close()
    return lines
```

### pty 模拟串口
```python
import os
import pty

def create_serial_pair():
    master_fd, slave_fd = pty.openpty()
    slave_name = os.ttyname(slave_fd)
    return master_fd, slave_name
```

### 串口收发测试
```python
@pytest.fixture
def virtual_serial():
    master_fd, slave_fd = pty.openpty()
    slave_name = os.ttyname(slave_fd)
    yield master_fd, slave_name
    os.close(master_fd)
    os.close(slave_fd)


def test_serial_receive(virtual_serial):
    master_fd, slave_name = virtual_serial

    def writer():
        time.sleep(0.3)
        os.write(master_fd, b"$GPGGA,123519,4807.038,N\r\n")

    t = threading.Thread(target=writer)
    t.start()

    ser = serial.Serial(slave_name, 9600, timeout=2)
    line = ser.readline()
    ser.close()
    t.join()

    assert line.startswith(b"$GPGGA")
```

### NMEA 测试（改造版，去掉 try/except pass）
```python
# 正常
def test_normal():
    result = parse_nmea(b"$GPGGA,123519,4807.038,N")
    assert result['type'] == '$GPGGA'
    assert result['fields'] == ['123519', '4807.038', 'N']


# 异常：用 match 精确匹配错误信息
@pytest.mark.parametrize("raw,msg", [
    (b"", "empty"),
    (b"\xff\xfe", "non-ascii"),
    (b"GPGGA,123519", "missing $"),
    (b"$GPGGA", "too few fields"),
])
def test_errors(raw, msg):
    with pytest.raises(ValueError, match=msg):
        parse_nmea(raw)


# 边界：全部应该成功，直接断言
@pytest.mark.parametrize("raw,field_count", [
    (b"$GPGGA,", 1),
    (b"$GPGGA," + b"x" * 1000, 1),
    (b"$GPGGA,123519", 1),
    (b"$GPGGA,1,2,3,4,5,6,7,8,9,10", 10),
])
def test_boundary(raw, field_count):
    result = parse_nmea(raw)
    assert result['type'] == '$GPGGA'
    assert len(result['fields']) == field_count
```

---

## 四、测试用例设计记录

| 输入 | 期望 | 类别 | 结果 |
|---|---|---|---|
| `b"$GPGGA,123519,4807.038,N\r\n"` | type=$GPGGA | 正常 | 通过 |
| `b""` | ValueError("empty") | 异常-空 | 通过 |
| `b"\xff\xfe"` | ValueError("non-ascii") | 异常-编码 | 通过 |
| `b"GPGGA,123519\r\n"` | ValueError("missing $") | 异常-前缀 | 通过 |
| `b"$GPGGA\r\n"` | ValueError("too few fields") | 异常-字段少 | 通过 |
| `b"$GPGGA,\r\n"` | 1 个字段 | 边界-最少 | 通过 |
| `b"$GPGGA," + b"x"*1000` | 1 个字段 | 边界-超长 | 通过 |

---

## 五、今天写的文件

| 文件 | 内容 |
|---|---|
| `src/nmea_parser.py` | NMEA 解析 |
| `tests/test_nmea_parser.py` | 四种场景测试 |
| `src/serial_reader.py` | pyserial 读多行 |
| `src/serial_simulator.py` | pty 创建虚拟串口 |
| `tests/test_serial_io.py` | 串口收发测试 |
| `src/data_fusion.py` | 数据融合 |
| `tests/test_data_fusion.py` | 融合测试 |

---

## 六、遇到的问题 & 解决

| 问题 | 原因 | 解决 |
|---|---|---|
| `ImportError: No module named 'nmea_parser'` | `sys.path` 没加 src | 加 `sys.path.insert(0, ...)` |
| `from nmea_parser import nmea_parser` | 模块名和函数名搞混 | 改成 `from nmea_parser import parse_nmea` |
| `NameError: name 'parse_nmea' is not defined` | 导入名字不对 | 统一用 `parse_nmea` |
| `try/except: pass` 反模式 | 异常被吞，测试永远通过 | 明确断言成功或 `pytest.raises` |

---

## 七、迁移到工作电脑（QTest / GTest）

| Python / pytest | QTest / GTest | 说明 |
|---|---|---|
| `@pytest.fixture` | `initTestCase()` / `SetUp()` | 前置 |
| `yield` 后代码 | `cleanupTestCase()` / `TearDown()` | 后置 |
| `pytest.raises(ValueError)` | `EXPECT_THROW` | 测异常 |
| `@pytest.mark.parametrize` | `_data() + QFETCH` | 数据驱动 |
| `assert x == y` | `QCOMPARE(x, y)` | 断言 |
| `pytest -v` | `ctest --output-on-failure` | 跑测试 |
| `pyserial` | Qt SerialPort / termios | 串口 |
| `socket` | QUdpSocket / QTcpSocket | 网络 |

---

## 八、关键教训

1. **测试里不要写 `try/except: pass`**  
   它让"应该失败的情况"悄悄通过，测试就失去意义。每个用例必须有明确预期：要么成功（assert），要么失败（pytest.raises）。

2. **异常测试用 `match=` 精确匹配**  
   ```python
   with pytest.raises(ValueError, match="empty"):
       parse_nmea(b"")
   ```
   避免"错误的异常也让测试通过"。

3. **源码 bug 会被测试暴露**  
   比如 `.strip()` 处理不了 `\r`，`$GPGGA,N\r` 会残留 `\r`。测试时要么在输入里去掉 `\r\n`，要么改源码。

4. **pty 只是练手工具**  
   到岗后 `slave_name` 换成 `/dev/ttyUSB0`，其他代码基本不变。

---

## 九、自我验收

- [x] 能解释 fixture 的 yield 前后各做什么
- [x] 能用 fixture 管理串口/测试数据
- [x] 能用 pyserial 打开、读、写、关闭
- [x] 能用 pty 在 Mac 上模拟串口
- [x] 能写出串口测试四种场景
- [x] 能写数据融合测试
- [x] 知道 ImportError 和 NameError 的区别
- [x] 知道 `try/except: pass` 为什么是反模式

---

## 十、明天计划

- [ ] 学 CI：GitHub Actions 或 GitLab CI
- [ ] 把 pytest 串到 CI 里
- [ ] 学 cppcheck 静态分析
- [ ] 把 C++ 项目接入 CI（为到岗后用 QTest 做准备）

---

## 十一、参考

- pytest 官方文档 Fixtures
- pyserial 官方文档
- Python pty 模块文档
- NMEA 0183 协议简介
```

保存退出：`Ctrl+O` → 回车 → `Ctrl+X`。

提交：

```bash
cd ~/device-test-learning
git add .
git commit -m "day2: fixture + serial + nmea + data fusion + notes"
git push
```

---
