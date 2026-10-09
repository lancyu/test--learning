
# Day 4 - GTest + clang-tidy + C++ 测试

**日期：** 2026-10-9 
**学习时长：** 4 小时  
**今日目标：** 用 GTest 写 C++ 单元测试，学 clang-tidy 静态分析，把 C++ 测试接入 CI。

---

## 一、GTest 是什么

Google 出的 C++ 单元测试框架。

### 和 pytest 对照

| Python | C++ |
|---|---|
| pytest | GTest |
| `assert x == y` | `EXPECT_EQ(x, y)` |
| `def test_xxx():` | `TEST(SuiteName, TestName)` |
| `@pytest.fixture` | `SetUp()` / `TearDown()` |
| `pytest.raises` | `EXPECT_THROW` |
| `@pytest.mark.parametrize` | `TEST_P` + `INSTANTIATE_TEST_SUITE_P` |

### Mac 安装

```bash
brew install googletest
```

验证：
```bash
ls /opt/homebrew/lib/libgtest*
```

---

## 二、std:: 速查表

C++ 标准库都在 `std` 命名空间里。

| std:: | 作用 | Qt 类比 |
|---|---|---|
| `std::string` | 字符串 | `QString` |
| `std::vector<T>` | 动态数组 | `QVector<T>` / `QList<T>` |
| `std::stringstream` | 字符串流 | `QTextStream` |
| `std::getline` | 按分隔符读 | `QString::split` |
| `std::stod` | 字符串转 double | `QString::toDouble` |
| `std::stoi` | 字符串转 int | `QString::toInt` |
| `.empty()` | 是否为空 | `.isEmpty()` |
| `.size()` | 元素个数 | `.size()` |
| `.push_back(x)` | 追加元素 | `.append(x)` |
| `std::invalid_argument` | 参数非法异常 | 无直接对应 |
| `std::out_of_range` | 越界异常 | 无直接对应 |

### 重要特性

`std::stod` 和 `std::stoi` **自动跳过前导空格**：

```cpp
std::stod(" 100")   // 返回 100.0
std::stoi(" 200")   // 返回 200
```

和 Python 的 `float()`、`int()` 行为一致。

---

## 三、项目结构

```
cpp_tests/
├── radar_parser.h          # 声明
├── radar_parser.cpp        # 实现
├── test_radar_parser.cpp   # 测试
└── CMakeLists.txt          # 构建配置
```

### radar_parser.h

```cpp
#ifndef RADAR_PARSER_H
#define RADAR_PARSER_H

#include <string>
#include <vector>
#include <stdexcept>

struct RadarPoint {
    double angle;
    double distance;
    int intensity;
};

std::vector<RadarPoint> parseRadar(const std::string& data);

RadarPoint parseRadarStrict(const std::string& data);

#endif
```

### CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.14)
project(cpp_tests)

set(CMAKE_CXX_STANDARD 17)

find_package(GTest REQUIRED)

enable_testing()

add_executable(test_radar_parser
    test_radar_parser.cpp
    radar_parser.cpp
)
target_link_libraries(test_radar_parser GTest::gtest_main)
add_test(NAME test_radar_parser COMMAND test_radar_parser)
```

### 构建和跑测试

```bash
cd ~/device-test-learning/cpp_tests
cmake -B build
cmake --build build
cd build && ctest --output-on-failure
```

---

## 四、GTest 核心写法

### 1. 普通测试

```cpp
TEST(RadarParser, NormalSingle) {
    auto points = parseRadar("45.0,100.5,200");
    ASSERT_EQ(points.size(), 1);
    EXPECT_DOUBLE_EQ(points[0].angle, 45.0);
    EXPECT_DOUBLE_EQ(points[0].distance, 100.5);
    EXPECT_EQ(points[0].intensity, 200);
}
```

| 部分 | 意思 |
|---|---|
| `TEST` | GTest 宏，定义测试 |
| `RadarParser` | 测试套件名 |
| `NormalSingle` | 测试名 |
| `auto` | 编译器自动推断类型 |
| `ASSERT_EQ(a, b)` | 断言相等，失败终止当前测试 |
| `EXPECT_EQ(a, b)` | 断言相等，失败继续 |
| `EXPECT_DOUBLE_EQ(a, b)` | double 相等，带浮点容差 |

### ASSERT vs EXPECT

| 宏 | 失败后 |
|---|---|
| `ASSERT_*` | 终止当前测试函数 |
| `EXPECT_*` | 继续跑，最后汇总 |

### 2. 断言异常

被测代码加一个会抛异常的函数：

```cpp
RadarPoint parseRadarStrict(const std::string& data) {
    if (data.empty()) {
        throw std::invalid_argument("empty data");
    }
    // ... 省略
    if (p.angle < 0 || p.angle > 360) {
        throw std::out_of_range("angle out of range");
    }
    return p;
}
```

测试：

```cpp
TEST(RadarParserStrict, EmptyThrows) {
    EXPECT_THROW(parseRadarStrict(""), std::invalid_argument);
}

TEST(RadarParserStrict, AngleOutOfRangeThrows) {
    EXPECT_THROW(parseRadarStrict("361,100,200"), std::out_of_range);
}

TEST(RadarParserStrict, NormalOk) {
    EXPECT_NO_THROW(parseRadarStrict("45.0,100.5,200"));
}
```

| 宏 | 作用 |
|---|---|
| `EXPECT_THROW(stmt, ExcType)` | 断言抛指定类型异常 |
| `EXPECT_NO_THROW(stmt)` | 断言不抛异常 |
| `EXPECT_ANY_THROW(stmt)` | 断言抛任意异常 |

对应 pytest：

```python
with pytest.raises(ValueError):
    parse_radar_strict("")
```

### 3. Fixture：前置 / 后置

```cpp
class RadarParserTest : public ::testing::Test {
protected:
    void SetUp() override {
        normalData = "45.0,100.5,200";
        multiData = "45.0,100.5,200;90.0,50.0,100";
    }

    void TearDown() override {
        // 清理资源
    }

    std::string normalData;
    std::string multiData;
};

// 用 TEST_F 而不是 TEST
TEST_F(RadarParserTest, NormalSingle) {
    auto points = parseRadar(normalData);
    ASSERT_EQ(points.size(), 1);
}

TEST_F(RadarParserTest, NormalMultiple) {
    auto points = parseRadar(multiData);
    ASSERT_EQ(points.size(), 2);
}
```

| 写法 | 说明 |
|---|---|
| `class XxxTest : public ::testing::Test` | 继承 GTest Test 类 |
| `void SetUp() override` | 每个测试前自动调用 |
| `void TearDown() override` | 每个测试后自动调用 |
| `TEST_F(FixtureName, TestName)` | 用 fixture 的测试 |
| fixture 类成员变量 | 所有 `TEST_F` 都能用 |

对应 pytest：

```python
@pytest.fixture
def radar_data():
    return "45.0,100.5,200"

def test_normal_single(radar_data):
    assert len(parse_radar(radar_data)) == 1
```

### 4. 数据驱动测试（参数化）

```cpp
class RadarParserParamTest
    : public ::testing::TestWithParam<std::tuple<std::string, int>> {};

TEST_P(RadarParserParamTest, ExpectedCount) {
    auto [data, expectedCount] = GetParam();   // C++17 结构化绑定
    auto points = parseRadar(data);
    EXPECT_EQ(static_cast<int>(points.size()), expectedCount);
}

INSTANTIATE_TEST_SUITE_P(
    BoundaryValues,
    RadarParserParamTest,
    ::testing::Values(
        std::make_tuple("0,0,0", 1),
        std::make_tuple("360,100,255", 1),
        std::make_tuple("361,100,200", 0),
        std::make_tuple("-1,100,200", 0),
        std::make_tuple("45,-5,200", 0),
        std::make_tuple("45,100,256", 0),
        std::make_tuple("45,100,-1", 0),
        std::make_tuple("45, 100, 200", 1)
    )
);
```

| 写法 | 说明 |
|---|---|
| `TEST_P` | 参数化测试宏 |
| `::testing::TestWithParam<T>` | 继承它，T 是参数类型 |
| `GetParam()` | 拿当前这组参数 |
| `INSTANTIATE_TEST_SUITE_P` | 实例化，提供所有参数 |
| `::testing::Values(...)` | 参数列表 |
| `std::tuple<T1, T2>` | 多参数组合 |
| `std::make_tuple(a, b)` | 创建 tuple |
| `auto [x, y] = GetParam()` | C++17 解构 |

对应 pytest：

```python
@pytest.mark.parametrize("data,expected_count", [
    ("0,0,0", 1),
    ("360,100,255", 1),
    ("361,100,200", 0),
    ("-1,100,200", 0),
])
def test_radar_parametrized(data, expected_count):
    assert len(parse_radar(data)) == expected_count
```

---

## 五、测试结果

今天跑了 27 个测试，全部通过：

| 测试套件 | 数量 |
|---|---|
| RadarParser | 11 |
| RadarParserStrict | 5 |
| RadarParserTest（fixture） | 3 |
| BoundaryValues/RadarParserParamTest | 8 |
| 合计 | 27 |

```
[==========] 27 tests from 4 test suites ran.
[  PASSED  ] 27 tests.
100% tests passed, 0 tests failed out of 1
```

---

## 六、clang-tidy 是什么

和 cppcheck 一样是静态分析工具，但更强。

| | cppcheck | clang-tidy |
|---|---|---|
| 谁做的 | 开源社区 | LLVM 官方 |
| 需要编译吗 | 不需要 | 需要 `compile_commands.json` |
| 检查项 | 161 个 | 400+ 个 |
| 自动修复 | 不支持 | 支持 `--fix` |
| 检查内容 | 通用 bug | 现代 C++ 写法、编码规范 |
| 适合场景 | 快速扫 | 深度分析 |

**到岗后两个都跑，结果互补。**

### Mac 安装

```bash
brew install llvm
```

clang-tidy 可能不在 PATH 里，需要加：

```bash
echo 'export PATH="/opt/homebrew/opt/llvm/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
clang-tidy --version
```

### 生成 compile_commands.json

```bash
cd ~/device-test-learning/cpp_tests
cmake -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

生成 `build/compile_commands.json`。

### 跑 clang-tidy

```bash
cd ~/device-test-learning/cpp_tests
clang-tidy radar_parser.cpp -p build/
```

| 参数 | 作用 |
|---|---|
| `radar_parser.cpp` | 要分析的文件 |
| `-p build/` | compile_commands.json 所在目录 |

### .clang-tidy 配置文件

放在项目根目录：

```yaml
Checks: >
  -*,
  bugprone-*,
  cppcoreguidelines-*,
  modernize-*,
  performance-*,
  readability-*
WarningsAsErrors: 'bugprone-*'
```

| 配置 | 意思 |
|---|---|
| `-*` | 先关掉所有检查 |
| `bugprone-*` | bug 易发类 |
| `cppcoreguidelines-*` | C++ 核心指南 |
| `modernize-*` | 现代化建议 |
| `performance-*` | 性能相关 |
| `readability-*` | 可读性相关 |
| `WarningsAsErrors` | 某类警告当错误 |

**为什么先 `-*`**：默认检查太多，先关掉再按需开，输出可控。

### 自动修复（先别用）

```bash
clang-tidy radar_parser.cpp -p build/ --fix
```

原因：
1. 自动修复可能改错
2. 还没看懂报告就改，学不到东西
3. 正式项目要 review 每处修改

---

## 七、遇到的问题 & 解决

| 问题 | 原因 | 解决 |
|---|---|---|
| `invalid preprocessing directive` | 把 Markdown 的 `#` 复制进 C++ | 改成 `//` 注释 |
| `BoundaryValues/...ExpectedCount/7` 失败 | 测试期望写成 0，实际是 1 | `std::stod` 会跳过空格，期望改成 1 |
| 编译失败但 ctest 显示 Passed | 跑的是旧的可执行文件 | 先确认编译成功，再跑 ctest |

### 关键教训

**测试挂了不代表代码有问题，有时候是测试自己写错了。**

区分两种情况：

| 情况 | 特征 | 处理 |
|---|---|---|
| 代码 bug | 期望对，实际错 | 改代码 |
| 测试写错 | 期望错，实际对 | 改测试 |

判断标准：**先弄清楚"正确的行为应该是什么"，再看代码和测试谁跟它不一致。**

如果业务上有分歧（比如带空格的数据该不该接受），正确做法是**提给开发或产品确认**，再决定改代码还是改测试。

---

## 八、CI 集成

等本地跑通后，把 GTest 和 clang-tidy 接入 CI。

### 加两个 job

```yaml
  gtest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt-get update && sudo apt-get install -y cmake libgtest-dev
      - run: |
          cd cpp_tests
          cmake -B build
          cmake --build build
      - run: |
          cd cpp_tests/build
          ctest --output-on-failure

  clang-tidy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt-get update && sudo apt-get install -y cmake clang-tidy
      - run: |
          cd cpp_tests
          cmake -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
      - run: |
          cd cpp_tests
          clang-tidy radar_parser.cpp -p build/ 2> clang_tidy.txt || true
          cat clang_tidy.txt
```

### 提交

```bash
cd ~/device-test-learning
git add .
git commit -m "day4: gtest + clang-tidy + ci"
git push
```

### 去 GitHub Actions 看

4 个 job 全部绿色：
- pytest ✅
- cppcheck ✅
- gtest ✅
- clang-tidy ✅

---

## 九、GTest 三件套速查

| 功能 | GTest | pytest |
|---|---|---|
| 普通测试 | `TEST(Suite, Name)` | `def test_xxx():` |
| 断言相等 | `EXPECT_EQ(a, b)` | `assert a == b` |
| 浮点相等 | `EXPECT_DOUBLE_EQ(a, b)` | `assert a == pytest.approx(b)` |
| 测异常 | `EXPECT_THROW(stmt, ExcType)` | `with pytest.raises(ExcType):` |
| 前置后置 | `class X : public ::testing::Test { SetUp/TearDown }` | `@pytest.fixture` |
| 用 fixture | `TEST_F(X, Name)` | 测试函数加 fixture 参数 |
| 参数化 | `TEST_P` + `INSTANTIATE_TEST_SUITE_P` | `@pytest.mark.parametrize` |

---

## 十、迁移到工作电脑

| 本地 Mac | 公司电脑 |
|---|---|
| `brew install googletest` | 公司 C++ 环境已有 |
| `cmake -B build` | 公司 CMake 配置 |
| `ctest` | 公司测试命令 |
| `clang-tidy` | 公司静态分析配置 |
| GitHub Actions | GitLab CI / Jenkins / 公司 CI |

核心不变：**写测试 → 跑测试 → 静态分析 → 看结果 → 接入 CI。**

---

## 十一、自我验收

- [x] 能解释 GTest 和 pytest 的对应关系
- [x] 能用 `TEST` 写普通测试
- [x] 能用 `EXPECT_THROW` 测异常
- [x] 能用 fixture 管理前置后置
- [x] 能用 `TEST_P` + `INSTANTIATE_TEST_SUITE_P` 写参数化测试
- [x] 能跑通 `cmake` + `ctest`
- [x] 知道 clang-tidy 和 cppcheck 的区别
- [x] 能生成 compile_commands.json
- [x] 能跑 clang-tidy 并解读报告
- [x] 知道测试挂了要先判断是代码问题还是测试问题

---

## 十二、明天计划

- [ ] 学 QTest（Qt 项目专用）
- [ ] QTest 的信号槽测试
- [ ] 覆盖率工具（gcov / lcov）
- [ ] Valgrind 内存检测
- [ ] 把 QTest 接入 CI

---

## 十三、参考

- GTest 官方文档
- clang-tidy 官方文档
- C++ Core Guidelines
- CMake 官方文档
```

保存退出：`Ctrl+O` → 回车 → `Ctrl+X`。

提交：

```bash
cd ~/device-test-learning
git add .
git commit -m "day4: gtest + clang-tidy + notes"
git push
```

---

## Day 4 完成

你现在有了：

| 能力 | 工具 |
|---|---|
| Python 测试 | pytest + fixture + parametrize |
| C++ 测试 | GTest + 断言 + fixture + 参数化 |
| 静态分析 | cppcheck + clang-tidy |
| CI | GitHub Actions |
| 串口/UDP | pyserial + socket + pty |

要不要继续 Day 5？Day 5 可以安排：

- QTest：Qt 项目专用测试框架，你的 Qt 背景直接用
- 信号槽测试：`QSignalSpy`
- GUI 事件模拟：`QTest::mouseClick()`
- 覆盖率工具：gcov / lcov
