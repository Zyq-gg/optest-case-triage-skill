# PyTorch 使用问题报告契约

创建或更新非工作簿的 PyTorch 使用问题分析文档时，完整阅读本文。该报告用于用户脚本、模型、命令、日志、性能、数值、安装、编译或分布式问题；不要套用工作簿行号和 pytest 专用标题。

## 目录

- [报告范围](#报告范围)
- [文档头](#文档头)
- [固定五节结构](#固定五节结构)
- [修改与验证一致性](#修改与验证一致性)
- [提交边界](#提交边界)
- [交付检查](#交付检查)
- [可移植模板](#可移植模板)

## 报告范围

- 默认一个逻辑问题使用一份报告；同一根因的多个现象可以分组，不同根因分开。
- 使用用户指定的报告路径。未指定时，在问题日志旁或当前任务目录创建 `pytorch_problem_<short-name>.md`。
- 问题来自 issue、工单或用户编号时，将该编号作为稳定身份；否则用清晰标题、入口命令和错误签名建立身份。
- 增量更新同一问题报告，保留正确历史；新验证改变结论时，更新状态并说明旧结论为何过时。
- 明确区分直接复现、等价/最小复现和仅日志静态分析。
- 问题涉及 guard、fallback、skip、禁用优化或 workaround 时，分别记录历史原始失败、当前遏制状态和目标修复状态；不能用当前不报错覆盖历史语义。

## 文档头

### 1. 问题身份和来源

记录：

- 问题标题/编号；
- 来源：当前环境、远程问题现场、日志、issue 或用户项目；
- 用户项目/入口路径；
- 原始工作目录和执行命令；
- API/operator/function、模型阶段或失败组件；
- 预期行为（用户提供、官方 contract 或明确标记的推断）；
- 实际行为和错误签名；
- 正常/失败版本和首次出现信息（如有）。

### 2. 执行环境

记录环境激活、Python、torch 版本、`torch.__file__`、accelerator/runtime、GPU/device、关键依赖、dtype/shape/backend/mode。可以引用 `collect_pytorch_env.py` 输出，但只保留与问题有关的信息。

### 3. 问题现场和仓库角色

使用以下表格；不适用的角色写 `未使用/不适用`，不能猜测：

| 角色 | 路径/连接 | branch/HEAD 或版本 | 状态与用途 | 提交边界 |
| --- | --- | --- | --- | --- |
| 用户项目/问题现场 | `<path or connection>` | `<state>` | `<原始命令/日志/只读或已修改>` | `<独立仓库或不提交>` |
| PyTorch 编译仓 | `<compile-repo>` | `<branch>/<HEAD>` | `<build/patch 状态>` | `build/验证副本不提交` |
| PyTorch 代码记录仓 | `<code-record-repo>` | `<branch>/<HEAD>` | `<dirty/remote/base>` | `PyTorch 唯一提交来源` |
| 安装验证仓 | `<torch.__file__ 所在目录>` | `<torch version>` | `<原始/已同步并保留的 validation-only patch>` | `不提交` |

同时记录：

- 代码记录仓 `origin`、`upstream`、`official` 的实际映射；
- 当前代码提交状态和目标分支；
- 编译仓与安装验证仓是否同步了相同 patch；
- 安装验证仓中哪些有效修改被保留给用户复测。
- 安装验证仓修改前后的文件 hash，以及与代码记录仓 runtime 文件的一致性检查结果。

存在 PyTorch 修改时，文档顶部使用一张权威逻辑修改表：

| 顺序 | 问题/根因 | 代码记录仓文件或 hunk | 验证副本 | 状态 |
| --- | --- | --- | --- | --- |
| 1 | `<root cause>` | `<paths/change>` | `<compile/install mirrors>` | `<已应用未提交 / 已提交 HASH / 已推送>` |

用户项目修改与 PyTorch 修改分开列表，不能放入同一个 commit 序号。

## 固定五节结构

每个逻辑问题使用一个 `##` 标题，标题下写问题身份和来源，然后严格保留以下五个 `###` 小节。

### 1. 问题现象与报错信息

包含：

- 用户问题描述和原始日志摘要；
- 原始命令、工作目录和入口；
- 当前复现命令及结果；
- 复现等级：原始、等价、最小或未复现；
- 错误签名或 hang/性能/内存/数值度量；
- 当前现象是否与原问题一致；
- warning 与真正失败条件的区别。
- 历史原始失败、当前 guard/fallback/workaround 状态和目标修复状态；不适用时明确写不适用。

只有日志时写 `仅日志分析，未在当前环境复现`。不能将错误消失直接等同于功能正确。

### 2. 预期行为与错误分析

包含：

- 用户提供的预期行为；未提供时写可信 contract 或标记推断；
- 输入、模型阶段、device/dtype/shape/backend/mode；
- 用户入口到 PyTorch API、dispatcher/compiler/runtime/backend 的调用链；
- 问题归属及支持证据；
- 使用/API、环境、用户项目、第三方、PyTorch、backend 等候选如何排除；
- 官方 `main`、release、issue、PR、commit 结论，再写内部 upstream；
- 最终根因和残余不确定性。
- 候选路径敏感问题的 eligibility、外层 guard、实际注册/生成/执行路径，以及当前通过是否被其他 candidate 或 fallback 掩盖。

性能和内存问题必须说明 baseline 与测量方法；数值问题说明 reference；hang 说明阻塞层和 timeout 证据。

### 3. 解决方法

开头用以下一种或多种明确状态：

- `配置修改`；
- `用户项目修改`；
- `依赖/安装修复`；
- `第三方扩展修改`；
- `已应用 PyTorch test-only 修改`；
- `已应用 PyTorch runtime/compiler/backend 修改`；
- `明确 unsupported`；
- `临时 workaround`；
- `仅诊断，未修改`；
- `未应用的可选方案`。

然后记录：

- 修改所属仓库和文件；
- PyTorch applied diff 必须从代码记录仓 Git 生成；
- 用户项目 diff 与 PyTorch diff 分开；
- 编译仓同步文件、基线和构建命令；
- 安装验证仓同步文件，以及是否保留供用户复测；
- 修改前后行为和与根因的因果关系；
- 影响和不影响的 device/dtype/shape/backend/API；
- 采用、适配或不采用官方方案的理由。
- 如果现状靠禁用路径或删除优化遏制问题，说明目标方案如何恢复原语义/性能，而不是把遏制措施冒充根因修复。

配置、环境和用户项目解决方案不能标为 PyTorch 源码修复。未应用 diff 必须显式标记，不能在下一节称为修复后验证。

### 4. 验证结果

记录：

- 环境激活、同步、构建和执行命令；
- 原始或等价复现结果；
- 可验证预期行为的 assertion/度量；
- PyTorch regression test 和相邻覆盖；
- 测试源码、编译产物和实际 runtime 来源；
- 静态检查；
- 未运行范围、blocker 和残余风险；
- 安装验证仓保留修改的路径和当前状态。
- candidate/dispatch/autotune 问题的路径证据：强制候选、生成代码、counter、日志或 profiler；自然通过不能替代该证据。
- 性能敏感正确性修复的 base/优化对照、非法适用域、fallback、自然选择、首次编译/资源淘汰和运行性能结果。

结果使用准确状态：`已修复并验证`、`配置后通过`、`环境修复后通过`、`workaround 后通过`、`仍失败`、`无法复现`、`无法验证`、`明确不支持`。skip/xfail 不能写成真实 PASS。

### 5. 提交建议

记录：

- 用户项目和 PyTorch 是否分别需要提交；
- 每个仓库的文件/hunk 边界；
- 必须保持 unstaged 的编译仓、安装验证仓、日志和无关修改；
- 建议 title 与 Why/What/Impact；
- 与每个 commit 对应的验证证据；
- 当前状态：无需提交、待提交、committed hash、pushed branch 或 MR source/target。

用户项目和 PyTorch 修改不得形成跨仓库 commit。配置/环境解决且无源码变化时写 `无需提交`。

## 修改与验证一致性

- PyTorch applied/submission diff 只来自代码记录仓。
- 编译仓和安装验证仓属于验证副本；安装验证仓中的有效修改可以保留，但不进入 Git 提交。
- 三处 patch 不一致时，列出差异，不能宣称验证了代码记录仓中的同一修复。
- 用户项目 diff 单独生成、单独验证、单独提交。
- 基线通过不能写成修复后通过；只验证 workaround 不能宣称根因已修复。
- 无异常不等于输出正确；按问题类型验证语义、数值、性能、内存或分布式完成条件。
- 强制目标 candidate 未实际进入时，不能把结果写成该 candidate 已验证；先检查 eligibility、外层 guard 和缓存。
- 要求保留性能优化时，删除候选、广泛 fallback 或硬编码失败 shape 只能标为 workaround，不能标为完整修复。

## 提交边界

- 只有用户明确要求才 commit、push 或准备 MR/PR。
- PyTorch commit 只从代码记录仓 stage。
- 用户项目需要提交时，在它自己的仓库单独处理，并再次确认目标 remote/branch。
- 编译仓 build 产物、临时 patch，安装验证仓保留 patch，日志、模型、数据、cache 和报告默认不提交。
- 提交后用真实 hash/subject 更新报告；push 后只记录实际 remote/branch，不把创建链接写成已创建 MR。

## 交付检查

交付前确认：

1. 问题身份、来源、命令和错误签名可追溯。
2. 直接/远程/日志现场以及复现等级准确。
3. 四类角色路径和提交边界明确，不适用项已标记。
4. 五个固定小节齐全且顺序正确。
5. 问题归属有证据，未把用户错误强行写成 PyTorch bug。
6. applied/proposed/config-only/workaround 状态与实际修改一致。
7. PyTorch diff 来自代码记录仓，用户项目 diff 与其分开。
8. 验证覆盖预期行为，不只检查异常消失。
9. 安装验证仓保留 patch 已记录，但未进入提交建议。
10. 命令、代码围栏、表格、链接、hash、branch 和状态一致。
11. 历史失败、当前遏制和目标修复没有混写；候选路径与性能保留证据符合问题目标。

## 可移植模板

````markdown
# PyTorch 使用问题分析：<问题标题或编号>

问题身份：

```text
来源: <当前环境 / 远程问题现场 / 日志 / issue>
用户项目/入口: <path or command>
预期行为: <用户提供 / contract / 推断 / 未确认>
实际行为: <error signature or measured symptom>
历史/当前/目标状态: <original failure / containment / repaired target>
```

运行环境：

```bash
<activation and working directory>
python3 <skill-dir>/scripts/collect_pytorch_env.py
```

| 角色 | 路径/连接 | branch/HEAD 或版本 | 状态与用途 | 提交边界 |
| --- | --- | --- | --- | --- |
| 用户项目/问题现场 | `<path>` | `<state>` | `<source/repro>` | `<independent>` |
| PyTorch 编译仓 | `<path or 不适用>` | `<state>` | `<build>` | `不提交验证产物` |
| PyTorch 代码记录仓 | `<path or 不适用>` | `<state>` | `<source diff>` | `PyTorch 唯一提交来源` |
| 安装验证仓 | `<torch package root>` | `<version>` | `<original or retained patch>` | `不提交` |

## <问题标题>

问题来源：`<source>`；问题身份：`<id/signature>`。

### 1. 问题现象与报错信息

<description, original log, reproduction level and exact command/result>

<historical failure, current containment and target-fix state when relevant>

### 2. 预期行为与错误分析

<expected contract, inputs, call path, ownership, evidence, official/internal findings>

<candidate eligibility and actual execution-path evidence when relevant>

### 3. 解决方法

状态：`<solution type>`

<configuration or repository-scoped diffs; compile/install synchronization; causal analysis>

### 4. 验证结果

```bash
<exact commands>
```

```text
<exact results and semantic checks>
```

<regression scope, runtime source, retained validation patch, residual risk>

<forced candidate, invalid-domain guard, fallback, natural selection and performance evidence when relevant>

### 5. 提交建议

<separate user-project/PyTorch boundaries, status, title/body, validation, hash/branch if completed>
````
