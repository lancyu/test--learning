

# Day 1 - pytest 测试基础

**日期：** 2026-10-08  
**学习时长：** 7 小时  
**今日目标：** 跑通 pytest，学会等价类、边界值、异常路径，能写出第一个测试用例。

---

## 一、今天学了什么

- assert 断言
- 测试函数命名规则：test_模块_场景_条件
- pytest.mark.parametrize 数据驱动
- pytest.raises 测异常
- 等价类、边界值、异常路径
- UDP 模拟接收与测试

---

## 二、核心概念理解

### 1. assert
确定输出与期望输出是否相等。条件为真继续，为假报错。
例如：
```python
assert len(result) == 1
assert result[0]['angle'] == 45.0
```

### 2. 等价类
把输入分成几类，每类取一个代表值测试。
比如角度字段可以分成：合法数字、非数字、空值、负数。

### 3. 边界值
测 0、最大值、最小值、刚好越界的值。
比如角度 0、360、361、-1。

### 4. 异常路径
空数据、格式错、字段缺失、非数字、前缀错误。
比如 GPS 语句不是 `$GPGGA` 开头，应该抛 `ValueError`。

---

## 三、关键代码 / 命令

### 常用命令
```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install pytest pytest-cov pyserial

# 跑所有测试
pytest -v

# 只跑某个测试文件
pytest tests/test_radar_parser.py -v

# 只跑某个测试函数
pytest tests/test_radar_parser.py::test_radar_normal_single -v

# 看覆盖率
pytest --cov=src --cov-report=term-missing

# 生成 HTML 覆盖率报告
pytest --cov=src --cov-report=html:reports/htmlcov
```

### 代码片段

**1. import 路径处理**
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# 把 src/ 加入模块搜索路径，否则 tests/ 里 import radar_parser 会失败
```

**2. 被测函数（radar_parser.py）**
```python
def parse_radar(data: str) -> list:
    """
    解析 "角度,距离,强度;角度,距离,强度;..."
    非法数据跳过，返回合法点列表
    """
    points = []
    if not data:
        return points

    for seg in data.split(';'):
        seg = seg.strip()
        if not seg:
            continue

        fields = seg.split(',')
        if len(fields) != 3:
            continue

        try:
            angle = float(fields[0])
            distance = float(fields[1])
            intensity = int(fields[2])
        except ValueError:
            continue

        if not (0 <= angle <= 360):
            continue
        if distance < 0:
            continue
        if not (0 <= intensity <= 255):
            continue

        points.append({
            'angle': angle,
            'distance': distance,
            'intensity': intensity,
        })

    return points
```

**3. 最简单的测试**
```python
def test_radar_normal_single():
    result = parse_radar("45.0,100.5,200")
    assert len(result) == 1
    assert result[0]['angle'] == 45.0
    assert result[0]['distance'] == 100.5
    assert result[0]['intensity'] == 200
```

**4. 数据驱动测试（parametrize）**
```python
@pytest.mark.parametrize("data,expected_len", [
    ("0,0,0", 1),                    # 边界最小
    ("360,100,255", 1),              # 边界最大
    ("361,100,200", 0),              # 角度越界
    ("-1,100,200", 0),               # 角度负数
    ("45,-5,200", 0),                # 距离负数
    ("45,100,256", 0),               # 强度越界
    ("45,100,-1", 0),                # 强度负数
    ("45, 100, 200", 1),             # 带空格
])
def test_radar_parametrized(data, expected_len):
    assert len(parse_radar(data)) == expected_len
```

**5. 测异常**
```python
def test_gps_invalid_prefix():
    with pytest.raises(ValueError):
        parse_gps("$GPRMC,123519,...")
# with pytest.raises(ValueError) = 上下文管理器
# 块内如果抛 ValueError，测试通过
# 块内没抛异常，测试失败
# 块内抛了别的异常，测试也失败
```

**6. UDP 接收（udp_receiver.py）**
```python
import socket
import json

def receive_one(bind_addr=("127.0.0.1", 0), timeout=2):
    """接收一个 UDP 包并返回解析后的字典"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(bind_addr)
    sock.settimeout(timeout)
    try:
        data, addr = sock.recvfrom(4096)
        return json.loads(data.decode()), addr, sock.getsockname()
    finally:
        sock.close()


def send_radar(target_addr, points):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = json.dumps({"type": "radar", "points": points}).encode()
    sock.sendto(payload, target_addr)
    sock.close()
```

**7. UDP 测试（多线程）**
```python
import threading
import time

def test_udp_receive_radar():
    result = {}

    def receiver():
        data, _, _ = receive_one(("127.0.0.1", 19999))
        result['data'] = data

    t = threading.Thread(target=receiver)  # 子线程负责接收
    t.start()
    time.sleep(0.2)                        # 等接收端就绪

    send_radar(("127.0.0.1", 19999), [
        {"angle": 45.0, "distance": 100.5, "intensity": 200}
    ])

    t.join(timeout=3)                      # 等子线程结束
    assert 'data' in result
    assert result['data']['type'] == 'radar'
    assert len(result['data']['points']) == 1


def test_udp_timeout():
    with pytest.raises(Exception):
        receive_one(("127.0.0.1", 19998), timeout=1)
```

---

## 四、测试用例设计记录

| 输入 | 期望输出 | 属于哪类 | 实际结果 |
|------|----------|----------|----------|
| `45.0,100.5,200` | 1 个点 | 正常 | 通过 |
| `45.0,100.5,200;90.0,50.0,100` | 2 个点 | 正常多点 | 通过 |
| `""` | 空列表 | 异常-空 | 通过 |
| `45.0,100.5` | 空列表 | 异常-字段缺失 | 通过 |
| `abc,100,200` | 空列表 | 异常-非数字 | 通过 |
| `0,0,0` | 1 个点 | 边界最小 | 通过 |
| `360,100,255` | 1 个点 | 边界最大 | 通过 |
| `361,100,200` | 空列表 | 边界越界 | 通过 |
| `-1,100,200` | 空列表 | 边界负数 | 通过 |
| `45,100,256` | 空列表 | 边界越界 | 通过 |

---

## 五、今天写的测试文件

| 文件 | 测试内容 | 用例数 |
|------|----------|--------|
| `tests/test_radar_parser.py` | 雷达解析正常/异常/边界 | 12 |
| `tests/test_udp.py` | UDP 接收模拟 | 2 |

覆盖率：`待填`

---

## 六、遇到的问题 & 解决

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| `test_radar-parser.py` 找不到 | 文件名用了连字符 | 改成下划线 `test_radar_parser.py` |
| `expected-len` 报错 | 变量名用了连字符 | 改成 `expected_len` |
| `collected 0 items` | 函数名没以 `test_` 开头 | 改名 |
| `ModuleNotFoundError` | `sys.path` 没加 `src` | 加 `sys.path.insert` |

---

## 七、迁移到工作电脑（QTest / GTest）

| Python / pytest | QTest / GTest | 备注 |
|-----------------|---------------|------|
| `assert x == y` | `QCOMPARE(x, y)` | 断言相等 |
| `assert len(r) == 1` | `QCOMPARE(r.size(), 1)` | 断言长度 |
| `assert r == []` | `QVERIFY(r.empty())` | 断言条件 |
| `@pytest.mark.parametrize` | `_data() + QFETCH` | 数据驱动 |
| `with pytest.raises(ValueError)` | `EXPECT_THROW(..., ...)` | 测异常 |
| `pytest -v` | `ctest --output-on-failure` | 跑测试 |

---

## 八、自我验收

- [x] 能跑通 `pytest -v`
- [x] 能说出等价类、边界值、异常路径
- [x] 能自己写出一个新测试用例
- [x] 知道 QTest 和 pytest 分别测什么
- [x] 笔记已提交 Git

---

## 九、明天计划

- [ ] 学 pyserial 模拟串口
- [ ] 学 socket 模拟 UDP
- [ ] 给串口解析函数写测试
- [ ] 了解覆盖率报告怎么读

---

## 十、参考

- pytest 官方文档 Getting Started
- pyserial 官方文档
- Python socket 官方文档
```

保存退出：`Ctrl+O` → 回车 → `Ctrl+X`。

然后提交：

```bash
cd ~/device-test-learning
git add docs/day1-testing.md
git commit -m "day1: notes"
git push
```