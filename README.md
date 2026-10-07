# device-test-learning

设备测试自学仓库 —— 用 Python + pytest 练测试基本功，为回到岗位后上手 Qt / QTest 打底。

模拟的对象是船舶/海洋电子设备里的两类典型数据：**雷达点数据**和 **GPS NMEA 语句**，
通信层用 UDP 模拟。都是纯代码，不依赖任何硬件。

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
| `pytest -v` | `ctest --output-on-failure` |

## 目录结构

```
src/
  radar_parser.py     雷达点解析 + GPGGA 语句解析（被测对象）
  udp_receiver.py     UDP 收一个包 / 发一组雷达点（被测对象）
tests/
  test_radar_parser.py  解析类测试：正常 / 异常 / 边界 / 数据驱动
  test_udp.py           UDP 收发测试，含超时异常
docs/
  day1-notes.md              pytest 学习笔记（含测试用例设计表、踩坑记录）
  mac命令练习笔记.md          macOS 终端命令练习
reports/                覆盖率 HTML 报告输出目录（git 已忽略内容）
```

## 快速开始

```bash
# 1. 建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 2. 装依赖
pip install pytest pytest-cov

# 3. 跑测试
pytest -v

# 4. 看覆盖率
pytest --cov=src --cov-report=term-missing
pytest --cov=src --cov-report=html:reports/htmlcov   # HTML 报告
```

## 当前状态

```
21 passed
src/radar_parser.py    34 stmts   100%
src/udp_receiver.py    16 stmts   100%
TOTAL                  50 stmts   100%
```

用例分布：

- `test_radar_parser.py` —— 12 个，覆盖单点/多点/空串/字段缺失/非数字/多余分号，
  以及 8 组 parametrize 边界数据（`0` 和 `360`、`361`、`-1`、强度 `255`/`256` 等）；
  GPGGA 部分测了正常解析、前缀错误、空串、字段不完整四种。
- `test_udp.py` —— 2 个，子线程收 + 主线程发验证雷达点下发；无数据时验证超时抛异常。

## 两个被测函数的协议

**雷达点** —— 分号分隔的多个点，每个点是 `角度,距离,强度`：

```
45.0,100.5,200;90.0,50.0,100
```

约束：角度 `0~360`、距离 `>= 0`、强度 `0~255`。**任何不合法的数据点直接跳过，不抛异常**，
返回所有合法点的字典列表。这是设备上真实解析逻辑的典型写法——脏数据不能中断整帧。

**GPS** —— 标准 `$GPGGA` 语句，格式不对就抛 `ValueError`：

```
$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
```

注意这两个函数**故意用了不同的错误策略**：雷达是"跳过坏的继续"，GPS 是"整体报错"。
测试时要清楚被测代码到底是哪种约定，别用错 `assert` 方式。

## 踩过的坑

| 现象 | 原因 |
|------|------|
| `test_radar-parser.py` 找不到 | 文件名用了连字符，Python 标识符不允许 |
| `expected-len` 报错 | 同上，变量名不能带连字符 |
| `collected 0 items` | 测试函数名没以 `test_` 开头，pytest 不收集 |
| `ModuleNotFoundError: radar_parser` | 没把 `src` 加进 `sys.path` |

`sys.path` 那行的处理方式：

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
```

## 待办

- [ ] pyserial 模拟串口收发，给串口解析函数补测试
- [ ] 读懂覆盖率 HTML 报告，区分行覆盖和分支覆盖
- [ ] 加 pytest fixture，消掉测试里重复的 `sys.path` 和端口号
- [ ] 找一个真实 NMEA 样本（比如 AIS 语句）补解析测试