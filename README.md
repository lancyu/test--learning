# device-test-learning

设备测试自学仓库 —— 从 Python + pytest 走到 C++ + GTest，为到岗后上手 Qt / QTest 打底。

模拟的对象是船舶/海洋电子设备里的典型数据：**雷达点数据**、**GPS / NMEA 语句**、
**串口数据**，通信层用 UDP 和pty 模拟。都是纯代码，不依赖任何真实硬件。

**同一个雷达解析器写了两遍**（Python 和 C++），用来对照两套测试框架的写法差异，
并验证两边行为一致。

## 目标

测试用例的思路（等价类、边界值、异常路径）与框架语法是相通的。
Python 侧打底，C++ 侧对照，Qt 那套只是再换一层皮：

| Python / pytest | C++ / GTest | Qt / QTest |
|-----------------|-------------|------------|
| `assert x == y` | `EXPECT_EQ(x, y)` | `QCOMPARE(x, y)` |
| `assert len(r) == 1` | `ASSERT_EQ(r.size(), 1)` | `QCOMPARE(r.size(), 1)` |
| `assert r == []` | `EXPECT_TRUE(r.empty())` | `QVERIFY(r.empty())` |
| `@pytest.mark.parametrize` | `TEST_P` + `INSTANTIATE_TEST_SUITE_P` | `_data()` + `QFETCH` |
| `with pytest.raises(ValueError)` | `EXPECT_THROW(..., type)` | `EXPECT_THROW(..., type)` |
| `@pytest.fixture` / `yield` 后置 | `SetUp()` / `TearDown()` | `initTestCase()` / `cleanupTestCase()` |
| `assert abs(a-b) < 1e-6` | `EXPECT_DOUBLE_EQ` / `EXPECT_NEAR` | `QVERIFY(qFuzzyCompare)` |
| `pytest -v` | `ctest --output-on-failure` | `ctest --output-on-failure` |
| `pyserial` | termios | Qt SerialPort |
| `socket` | BSD socket | QUdpSocket / QTcpSocket |

## 目录结构

```
src/                          Python 被测代码
  radar_parser.py     雷达点解析 + GPGGA 语句解析
  nmea_parser.py      通用 NMEA 解析（四道关：空 / 非 ASCII / 无$ / 字段少）
  data_fusion.py      多传感器数据融合（GPS + 罗经 + AIS）
  serial_reader.py    pyserial 读多行
  serial_simulator.py pty 创建虚拟串口对
  udp_receiver.py     UDP 收一个包 / 发一组雷达点
  example.cpp         ⚠️故意含 bug 的 cppcheck 演示样本，不要修、不要删（见下）
tests/                       Python 测试
  test_radar_parser.py  解析类测试：正常 / 异常 / 边界 / 数据驱动 / fixture
  test_nmea_parser.py   NMEA 四种场景 + 边界
  test_data_fusion.py   融合：全传感器 / 缺传感器 / 目标数边界
  test_serial_io.py     串口：正常 / 多行 / 超时 / 非法字节 / count=0
  test_udp.py           UDP 收发 + 超时异常
cpp_tests/                      C++ 被测代码 + 测试
  radar_parser.h/.cpp     雷达解析的 C++ 版，行为与 Python 版一致
  test_radar_parser.cpp   TEST / TEST_F / TEST_P / EXPECT_THROW 全套
  CMakeLists.txt          C++17 + GTest
docs/
  day1-notes.md       pytest 基础（等价类、边界值、异常路径）
  day2-notes.md       fixture + 串口 + NMEA + 数据融合
  day3-notes.md       CI + cppcheck 静态分析
  day4-notes.md       GTest + clang-tidy + C++ 测试
  mac命令练习笔记.md   macOS 终端命令练习
reports/                   覆盖率 HTML 报告输出目录（git 已忽略内容）
```

### ⚠️ `src/example.cpp` 是故意的坏样本

它有**两个刻意留下的 bug**，用来演示 cppcheck 能扫出什么（详见 `docs/day3-notes.md`）：

1. `divide(10, 0)` —— 除零
2. `arr[10] = 1` —— `arr` 只有 5 个元素，数组越界

**不要修，也不要删。** 修好了就失去演示意义。
它同时也是 CI 的活体验证：cppcheck job 扫到它会报警告，
`cpp_tests/` 的真代码则应该是干净的——两者一对比就知道静态分析有没有正常工作。

> 它放在 `src/` 而不是 `cpp_tests/`，是因为 day3 的 CI job 只扫 `src/`。
> 这是历史遗留的位置，两边都能扫到的情况下放哪都不影响检测。

## 快速开始

Python 侧：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest pytest-cov pyserial

pytest -v
pytest --cov=src --cov-report=term-missing
pytest --cov=src --cov-report=html:reports/htmlcov   # HTML 报告
```

C++ 侧（需要 GTest）：

```bash
brew install googletest          # 装 GTest

cd cpp_tests
cmake -S . -B build && cmake --build build
cd build && ctest --output-on-failure
```

> ⚠️ `cpp_tests/build/` 是编译产物，已在 `.gitignore` 里，不要手动加。
> CI 配置在 `.github/workflows/test.yml`。

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

C++ 侧`cpp_tests/test_radar_parser.cpp` —— **27 个**，与 Python 侧的雷达用例一一对应：

- `TEST` —— 11 个基础用例（正常 / 空 / 字段缺失 / 非数字 / 边界 / 越界）
- `TEST` + `EXPECT_THROW` —— 5 个 `parseRadarStrict` 异常用例
  （空数据、字段数错、非数字、角度越界、正常不抛）
- `TEST_F` —— 3 个，带 `SetUp`/`TearDown` 的 fixture 用法
- `TEST_P` + `INSTANTIATE_TEST_SUITE_P` —— 8 组参数化边界数据，
  对应 Python 的 `parametrize`，用了 C++17 结构化绑定

## 被测代码的协议与错误策略

**雷达点** —— 分号分隔的多个点，每个点是 `角度,距离,强度`：

```
45.0,100.5,200;90.0,50.0,100
```

约束：角度 `0~360`、距离 `>= 0`、强度 `0~255`。**任何不合法的数据点直接跳过，不抛异常**，
返回所有合法点的字典列表。这是设备上真实解析逻辑的典型写法——脏数据不能中断整帧。

**C++ 版多了一个严格模式** `parseRadarStrict`：不接受分号多数据点，
遇到非法数据**抛异常**（`invalid_argument` 格式错/ 非数字，`out_of_range` 数值越界）。
它和宽松版 `parseRadar` 共存，目的是把"两种错误策略"都测到——
真实项目里两种写法都常见。

**NMEA / GPGGA** —— 格式不对就抛 `ValueError`：

```
$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
```

`parse_nmea` 走四道关，顺序固定：空数据 → 非 ASCII → 无 `$` 前缀 → 逗号切分不足 2 段。

**串口** —— `read_lines(port, baudrate, count, timeout)` 读满 `count` 行，
超时返回 `b''` 的那些行会被 `if line` 跳过，因此实际返回行数可能少于 `count`。

⚠️ **这几个函数故意用了不同的错误策略**：宽松版雷达和 `read_lines` 是"跳过坏的继续"，
`parseRadarStrict`、NMEA 和 `fuse` 是"整体报错"。写测试前先读被测函数，别凭直觉猜用哪种断言。

**Python 与 C++ 版行为一致性**：已用同一组输入逐条对拍验证，
`"45, 100, 200"`（带空格）、空串、`";;"`、多点、边界、越界 7 种输入两边结果完全相同。
注意 `"45, 100, 200"` 里的空格两边都能处理（`std::stod` 会跳过前导空白）。

## 踩过的坑

| 现象 | 原因 |
|------|------|
| `test_radar-parser.py` 找不到 | 文件名用了连字符，Python 标识符不允许 |
| `expected-len` 报错 | 同上，变量名不能带连字符 |
| `collected 0 items` | 测试函数名没以 `test_` 开头，pytest 不收集 |
| `ModuleNotFoundError: radar_parser` | 没把 `src` 加进 `sys.path` |
| `NameError: parse_nmea is not defined` | 模块名和函数名搞混，写成了 `from nmea_parser import nmea_parser` |
| 笔记里的 `git add` 报pathspec 错 | 文件名多了空格：实际是 `day2-notes.md` |
| `cmake: command not found` | cmake 装在 homebrew 但不在 PATH，用绝对路径 `/opt/homebrew/bin/cmake` |
| `No such file or directory: /opt/homebrew/bin/c++` | 编译器不叫 `c++`，本机是 `/usr/bin/clang++` |

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

### C++ 侧的两个注意点

**1. 旧的 build 目录不能当验证结果。** `cpp_tests/build/` 里留着上次编译的二进制，
直接跑它是绿的，但不代表当前源码能编译通过。要验证得重新构建：

```bash
cd cpp_tests && cmake -S . -B build && cmake --build build && ctest --output-on-failure
```

**2. `ASSERT_EQ` 与 `EXPECT_EQ` 的区别**：前者失败就终止当前测试函数，
后者继续往下跑。测返回值大小时用 `EXPECT_*`，测前置条件（size 是不是 1）用 `ASSERT_*`，
否则 size 不对时继续访问 `points[0]` 会越界 crash，而不是给出可读的失败信息。

## CI

`.github/workflows/test.yml` 目前跑两个 job：

- **pytest** —— Ubuntu + Python 3.11，装 `pytest pyserial pytest-cov` 后跑 `pytest -v`
- **cppcheck** —— `--enable=all --suppress=missingInclude src/` 扫 `src/`

⚠️ **当前缺口**：`cppcheck` 只扫了 `src/`（Python 代码基本扫不出什么），
**`cpp_tests/` 下的 C++ 代码没有任何 CI 覆盖** —— 既没跑 GTest，也没被静态分析扫到。
Day4 新增 C++ 测试后这个缺口就出现了，待补。

## 待办

- [x] pyserial 模拟串口收发，给串口解析函数补测试
- [x] GTest 入门：`TEST` / `TEST_F` / `TEST_P` / `EXPECT_THROW` 全套上手
- [x] CI 跑通：pytest job + cppcheck job（day3）
- [ ] **给 CI 加 C++ job**：编译 GTest + 跑 ctest + cppcheck 扫 `cpp_tests/`（当前缺口）
- [ ] 把 `pytest --cov=src` 接进 CI，产出覆盖率报告
- [ ] 修 `test_nmea_parser.py::test_boundary` 里的 `try/except: pass`
      （Day2 笔记自己把它列为反模式，也给了改法）
- [ ] 读懂覆盖率 HTML 报告，区分行覆盖和分支覆盖
- [ ] 把重复的 `sys.path` 挪到 `conftest.py`，给端口号做隔离，避免并行测试冲突
- [ ] 找一个真实 NMEA 样本（比如 AIS 语句）补解析测试
- [ ] 装 cppcheck / clang-tidy，本地跑一遍再对照 CI 报告