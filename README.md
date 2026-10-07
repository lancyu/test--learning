# device-test-learning

设备测试自学仓库 —— 用 Python + pytest 练测试基本功，为回到岗位后上手 Qt / QTest 打底。

模拟的对象是船舶/海洋电子设备里的典型数据：**雷达点数据**、**GPS / NMEA 语句**、
**串口数据**，通信层用 UDP 和 pty 模拟。都是纯代码，不依赖任何真实硬件。

## 目标

测试用例的思路（等价类、边界值、异常路径）和 Python 语法是相通的，
把这两块先练熟，工作电脑上换成 C++/Qt 只需要换一层皮：

| Python / pytest | C++ / QTest |
|-----------------|-------------|
| `assert x == y` | `QCOMPARE(x, y)` |
| `assert len(r) == 1` | `QCOMPARE(r.size(), 1)` |
| `assert r == []` | `QVERIFY(r.empty())` |
| `@pytest.mark.parametrize` | `_data() + QFETCH` |
| `with pytest.raises(ValueError)` | `EXPECT_THROW(..., ...)` |
| `@pytest.fixture` / `yield` 后置 | `initTestCase()` / `cleanupTestCase()` |
| `pytest.raises(..., match="empty")` | `EXPECT_THROW` + 校验错误码 |
| `pytest -v` | `ctest --output-on-failure` |
| `pyserial` | Qt SerialPort / termios |
| `socket` | QUdpSocket / QTcpSocket |

## 目录结构

```
src/
  radar_parser.py     雷达点解析 + GPGGA 语句解析
  nmea_parser.py      通用 NMEA 语句解析（四道关：空 / 非 ASCII / 无$ / 字段少）
  data_fusion.py      多传感器数据融合（GPS + 罗经 + AIS）
  serial_reader.py    pyserial 读多行
  serial_simulator.py pty 创建虚拟串口对
  udp_receiver.py     UDP 收一个包 / 发一组雷达点
tests/
  test_radar_parser.py  解析类测试：正常 / 异常 / 边界 / 数据驱动 / fixture
  test_nmea_parser.py   NMEA 四种场景 + 边界
  test_data_fusion.py   融合：全传感器 / 缺传感器 / 目标数边界
  test_serial_io.py     串口：正常 / 多行 / 超时 / 非法字节 / count=0
  test_udp.py           UDP 收发 + 超时异常
docs/
  day1-notes.md              pytest 基础（等价类、边界值、异常路径）
  day2-notes.md              fixture + 串口 + NMEA + 数据融合
  mac命令练习笔记.md          macOS 终端命令练习
reports/                覆盖率 HTML 报告输出目录（git 已忽略内容）
```

## 快速开始

```bash
# 1. 建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 2. 装依赖
pip install pytest pytest-cov pyserial

# 3. 跑测试
pytest -v

# 4. 看覆盖率
pytest --cov=src --cov-report=term-missing
pytest --cov=src --cov-report=html:reports/htmlcov   # HTML 报告
```

## 当前状态

```
43 passed
src/data_fusion.py       4 stmts   100%
src/nmea_parser.py      13 stmts   100%
src/radar_parser.py     34 stmts   100%
src/serial_reader.py    11 stmts   100%
src/serial_simulator.py  6 stmts   100%
src/udp_receiver.py     16 stmts   100%
TOTAL                   84 stmts   100%
```

用例分布：

- `test_radar_parser.py` —— 19 个，覆盖单点/多点/空串/字段缺失/非数字/多余分号，
  以及 8 组 parametrize 边界数据（`0` 和 `360`、`361`、`-1`、强度 `255`/`256` 等）；
  GPGGA 部分测了正常解析、前缀错误、空串、字段不完整四种。
  重复出现的测试数据已提取成 `radar_data` / `radar_points_multi` / `gga_sentence` 三个 fixture。
- `test_nmea_parser.py` —— 8 个，正常 1 + 异常 4 + 边界 3（超长字段、最少字段等）。
- `test_data_fusion.py` —— 7 个，全传感器、缺罗经、缺 AIS、缺 GPS 报错，
  目标数按 0/1/10/100 做参数化。
- `test_serial_io.py` —— 7 个，`read_lines` 的多行 / 单行 / 超时 / `count=0` /
  非 ASCII 字节忽略，加 `create_serial_pair` 自身检查。
- `test_udp.py` —— 2 个，子线程收 + 主线程发验证雷达点下发；无数据时验证超时抛异常。

## 被测代码的协议与错误策略

**雷达点** —— 分号分隔的多个点，每个点是 `角度,距离,强度`：

```
45.0,100.5,200;90.0,50.0,100
```

约束：角度 `0~360`、距离 `>= 0`、强度 `0~255`。**任何不合法的数据点直接跳过，不抛异常**，
返回所有合法点的字典列表。这是设备上真实解析逻辑的典型写法——脏数据不能中断整帧。

**NMEA / GPGGA** —— 格式不对就抛 `ValueError`：

```
$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
```

`parse_nmea` 走四道关，顺序固定：空数据 → 非 ASCII → 无 `$` 前缀 → 逗号切分不足 2 段。

**串口** —— `read_lines(port, baudrate, count, timeout)` 读满 `count` 行，
超时返回 `b''` 的那些行会被 `if line` 跳过，因此实际返回行数可能少于 `count`。

⚠️ **这几个函数故意用了不同的错误策略**：雷达和 `read_lines` 是"跳过坏的继续"，
NMEA 和 `fuse` 是"整体报错"。写测试前先读被测函数，别凭直觉猜用哪种断言。

## 踩过的坑

| 现象 | 原因 |
|------|------|
| `test_radar-parser.py` 找不到 | 文件名用了连字符，Python 标识符不允许 |
| `expected-len` 报错 | 同上，变量名不能带连字符 |
| `collected 0 items` | 测试函数名没以 `test_` 开头，pytest 不收集 |
| `ModuleNotFoundError: radar_parser` | 没把 `src` 加进 `sys.path` |
| `NameError: parse_nmea is not defined` | 模块名和函数名搞混，写成了 `from nmea_parser import nmea_parser` |
| 笔记里的 `git add` 报pathspec 错 | 文件名多了空格：实际是 `day2-notes.md` |

`sys.path` 那行的处理方式：

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
```

### 一个值得记住的教训：测试全绿 ≠ 测到了东西

Day2 最初有一版 `test_serial_io.py`，全绿，但它自己重抄了一遍 `pty.openpty()`，
**从没import 过 `src/serial_reader.py` 和 `src/serial_simulator.py`**——
两个源文件覆盖率都是 0%，等于一行没跑到。

验证方法很简单：把源文件临时移走，再跑测试。

```bash
mv src/serial_reader.py /tmp/ && pytest -q ; mv /tmp/serial_reader.py src/
```

如果测试**照样全过**，说明它根本没测到这个文件。改完再验一次：
移走后应该立刻报 `ModuleNotFoundError`，那才叫真的测上了。

覆盖率报告里的 `0%` 和 `Missing 2-13` 就是这种断开的直接信号，不要忽略。

## 待办

- [x] pyserial 模拟串口收发，给串口解析函数补测试
- [ ] 修 `test_nmea_parser.py::test_boundary` 里的 `try/except: pass`
      （Day2 笔记自己把它列为反模式，也给了改法）
- [ ] 读懂覆盖率 HTML 报告，区分行覆盖和分支覆盖
- [ ] 把重复的 `sys.path` 挪到 `conftest.py`，给端口号做隔离，避免并行测试冲突
- [ ] 找一个真实 NMEA 样本（比如 AIS 语句）补解析测试
- [ ] 接 GitHub Actions，把 `pytest --cov` 跑在 CI 上