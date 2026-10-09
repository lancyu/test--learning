下面是 Day 3 的完整笔记，直接复制到 `docs/day3-notes.md`。


# Day 3 - CI + cppcheck 静态分析

**日期：** 2026-10-8  
**学习时长：** 2 小时  
**今日目标：** 理解 CI，把 pytest 和 cppcheck 串进 GitHub Actions，能读懂 cppcheck 报告。

---

## 一、CI 是什么

### 大白话
CI = Continuous Integration = 持续集成。

> 你写完代码，往 Git 仓库一推，服务器自动帮你跑测试、检查代码、告诉你有没有问题。

### 没有 CI vs 有 CI

没有 CI：
```
写完代码 → 推到 Git
手动跑 pytest → 通过
手动跑 cppcheck → 有警告
手动跑构建 → 失败
手动告诉同事 → "我改好了"
```

有 CI：
```
写完代码 → 推到 Git
CI 自动：拉代码 → 装依赖 → 跑 pytest → 跑 cppcheck → 显示结果
打开网页一看：全绿 ✅ 或 有红 ❌
```

### 类比
CI 就像外卖平台的自动审核：你提交订单（代码），平台（CI）自动检查商家资质、菜品违规、配送范围，有问题拦下来，没问题放行。

### CI 工具
| 工具 | 谁用 | 特点 |
|---|---|---|
| GitHub Actions | GitHub 仓库 | 免费、YAML 配置、最简单 |
| GitLab CI | GitLab 仓库 | 企业常用、功能强 |
| Jenkins | 自建服务器 | 老牌、配置复杂 |

---

## 二、GitHub Actions 核心概念

| 概念 | 意思 |
|---|---|
| workflow | 一条流水线，对应一个 yml 文件 |
| job | 流水线里的一个任务 |
| step | 任务里的一步 |
| runner | 跑流水线的服务器 |
| trigger（on） | 什么时候触发，比如 push、pull_request |

### 配置文件位置
```
.github/workflows/test.yml
```
注意是 `.github` 不是 `github`，前面有个点。

---

## 三、今天写的 CI 配置

### `.github/workflows/test.yml`

```yaml
name: test

on: [push, pull_request]

jobs:
  pytest:
    runs-on: ubuntu-latest

    steps:
      - name: 拉代码
        uses: actions/checkout@v4

      - name: 装 Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: 装依赖
        run: pip install pytest pyserial pytest-cov

      - name: 跑测试
        run: pytest -v

  cppcheck:
    runs-on: ubuntu-latest

    steps:
      - name: 拉代码
        uses: actions/checkout@v4

      - name: 装 cppcheck
        run: sudo apt-get update && sudo apt-get install -y cppcheck

      - name: 跑静态分析
        run: cppcheck --enable=all --suppress=missingInclude src/ 2> cppcheck.txt || true

      - name: 显示报告
        run: cat cppcheck.txt
```

### 逐行翻译

| 配置 | 意思 |
|---|---|
| `name: test` | 流水线名字 |
| `on: [push, pull_request]` | push 或提 PR 时触发 |
| `jobs:` | 定义任务列表 |
| `pytest:` | 任务名叫 pytest |
| `runs-on: ubuntu-latest` | 跑在 Ubuntu 服务器上 |
| `steps:` | 步骤列表 |
| `actions/checkout@v4` | 拉代码 |
| `actions/setup-python@v5` | 装 Python |
| `pip install ...` | 装依赖 |
| `pytest -v` | 跑测试 |
| `cppcheck --enable=all ...` | 跑静态分析 |
| `|| true` | 即使 cppcheck 有警告也不让 job 失败 |

---

## 四、今天写的 C++ 文件

### `src/example.cpp`

```cpp
int divide(int a, int b) {
    return a / b;
}

int main() {
    int arr[5];
    arr[10] = 1;
    return divide(10, 0);
}
```

这个文件故意写了两个 bug，用来演示 cppcheck 能扫出什么。

---

## 五、CI 跑成功的证据

打开：
```
https://github.com/lancyu/test--learning/actions
```

看到：
- ✅ pytest job 绿
- ✅ cppcheck job 绿

pytest job 步骤：
```
Set up job        ✅ 1s
拉代码            ✅ 0s
装 Python         ✅ 0s
装依赖            ✅ 3s
跑测试            ✅ 8s
Post 装 Python    ✅ 0s
Post 拉代码       ✅ 0s
Complete job      ✅ 1s
```

43 个测试全过。

---

## 六、cppcheck 是什么

### 定义
**不运行代码，直接看源码找问题。**

比如：
```cpp
int divide(int a, int b) {
    return a / b;   // b 可能是 0，cppcheck 会警告
}
```
cppcheck 不用运行，直接扫源码就发现 `b` 没判空。

### 静态分析 vs 单元测试

| | 静态分析 | 单元测试 |
|---|---|---|
| 运行代码吗 | 不运行 | 运行 |
| 找什么问题 | 潜在 bug、编码规范 | 逻辑错误 |
| 什么时候跑 | 提交代码时 | 提交代码时 |
| 工具 | cppcheck、clang-tidy | QTest、GTest、pytest |

两者互补，都要有。

### 常用命令
```bash
cppcheck --enable=all --suppress=missingInclude --std=c++17 src/ 2> cppcheck.txt
```

| 参数 | 作用 |
|---|---|
| `--enable=all` | 开启所有检查 |
| `--suppress=missingInclude` | 忽略头文件找不到的警告 |
| `--std=c++17` | 指定 C++ 标准 |
| `2> cppcheck.txt` | 错误输出重定向到文件 |

---

## 七、cppcheck 报告解读

今天 cppcheck 扫 `src/example.cpp`，输出：

```
src/example.cpp:7:8: error: Array 'arr[5]' accessed at index 10, which is out of bounds. [arrayIndexOutOfBounds]
src/example.cpp:2:14: error: Division by zero. [zerodiv]
src/example.cpp:7:13: style: Variable 'arr[10]' is assigned a value that is never used. [unreadVariable]
nofile:0:0: information: Unmatched suppression: missingInclude [unmatchedSuppression]
nofile:0:0: information: Active checkers: 161/592 [checkersReport]
```

### 逐条解读

| 行 | 级别 | 问题 | 对应代码 | 处理 |
|---|---|---|---|---|
| 7 | error | 数组越界 `arr[10]` | `int arr[5]; arr[10] = 1;` | 提给开发，必须修 |
| 2 | error | 除以零 `a/b` | `return a / b;` 且传了 `0` | 提给开发，必须修 |
| 7 | style | 赋值后未使用 | `arr[10] = 1;` 后面没读 | 记录，低优先级 |
| - | information | 未匹配抑制 | 抑制了 `missingInclude` 但没触发 | 忽略 |
| - | information | 检查器报告 | 161/592 个检查器启用 | 忽略 |

### 报告格式
```
文件:行:列: 级别: 信息 [检查项ID]
```

### 级别对应处理

| 级别 | 意思 | 处理 |
|---|---|---|
| `error` | 确定的问题 | 提给开发，必须修 |
| `warning` | 可能的问题 | 判断，可能真可能误报 |
| `style` | 代码风格 | 记录，低优先级 |
| `information` | 提示信息 | 忽略 |

---

## 八、遇到的问题 & 解决

| 问题 | 原因 | 解决 |
|---|---|---|
| `fatal: unable to access ... Error in the HTTP2 framing layer` | Git 网络问题 | `git config --global http.version HTTP/1.1` |
| `refusing to allow a Personal Access Token to create or update workflow` | token 没有 workflow 权限 | 重新生成 token，勾上 `workflow` |
| `Warning: Node.js 20 is deprecated` | GitHub 内部版本过渡 | 忽略，不影响功能 |
| `Unmatched suppression: missingInclude` | 抑制了没触发的警告 | 忽略 |

### HTTP2 报错详解
GitHub 的 HTTP/2 协议在某些网络下不稳定，强制用 HTTP/1.1 解决：
```bash
git config --global http.version HTTP/1.1
```

### token 权限详解
GitHub 规定：任何涉及 `.github/workflows/` 的改动，必须用带 `workflow` 权限的 token。

生成 token 时要勾：
- `repo`
- `workflow`

---

## 九、到岗后怎么用

### 日常工作流
```
早上到公司
  ↓
git pull          拉最新代码
  ↓
改代码 / 写测试
  ↓
git add / commit / push
  ↓
CI 自动跑
  ↓
打开网页看结果
  ├── 绿 ✅ → 继续干活
  └── 红 ❌ → 点进去看日志 → 修 → 再 push
```

### 处理 cppcheck 报告的流程
```
1. 跑 cppcheck
   cppcheck --enable=all --suppress=missingInclude --std=c++17 src/ 2> cppcheck.txt

2. 打开报告

3. 逐条看级别
   ├── error       → 提给开发，附行号和代码
   ├── warning     → 判断，可能真问题也可能误报
   ├── style       → 记录，汇总后统一提
   └── information → 忽略

4. 整理成表格，发给开发

| 文件 | 行号 | 级别 | 问题 | 建议 |
|---|---|---|---|---|
| radar_parser.cpp | 45 | error | 数组越界 | 检查下标范围 |
| radar_parser.cpp | 78 | warning | 变量未初始化 | 加初始化 |
```

### 判断警告优先级
1. 会不会导致功能错误？会 → 修
2. 会不会导致 CI 失败？会 → 修
3. 只是提示未来会弃用？→ 记录，排期修

---

## 十、迁移到工作电脑

| 本地 Mac | 公司电脑 |
|---|---|
| GitHub Actions | GitLab CI / Jenkins / GitHub Actions |
| `pytest -v` | 公司测试命令 |
| `cppcheck src/` | 公司 C++ 项目路径 |
| `.github/workflows/test.yml` | 公司 CI 配置文件 |

核心逻辑不变：**代码提交 → CI 自动跑测试和静态分析 → 看结果。**

---

## 十一、自我验收

- [x] 能解释 CI 是什么
- [x] 能看懂 GitHub Actions 的 yml
- [x] 能写出一个 workflow
- [x] 知道 workflow / job / step 区别
- [x] 会用 cppcheck 跑静态分析
- [x] 知道 cppcheck 和单元测试的区别
- [x] 能读懂 cppcheck 报告的级别
- [x] 会判断 CI 警告的优先级

---

## 十二、明天计划

- [ ] 学 GTest 写 C++ 单元测试
- [ ] 学 QTest（Qt 项目）
- [ ] 学 clang-tidy 静态分析
- [ ] 把 C++ 测试接入 CI

---

## 十三、参考

- GitHub Actions 官方文档
- cppcheck 官方文档
- GitHub Actions Node.js 20 弃用公告
```

保存退出：`Ctrl+O` → 回车 → `Ctrl+X`。

提交：

```bash
cd ~/device-test-learning
git add .
git commit -m "day3: ci + cppcheck + notes"
git push
```

---
