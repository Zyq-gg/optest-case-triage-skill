# Markdown 分析报告契约

创建或更新工作簿对应的 Markdown 分析报告时，必须完整阅读本文。规则适用于不同环境和工作簿；不得从旧报告照抄实际路径、分支、sheet、行号、设备、版本或 case 名。

## 目录

- [报告范围与顺序](#报告范围与顺序)
- [文档头必备内容](#文档头必备内容)
- [case-固定结构](#case-固定结构)
- [代码-diff-要求](#代码-diff-要求)
- [提交信息要求](#提交信息要求)
- [一致性检查](#一致性检查)
- [可移植模板](#可移植模板)

## 报告范围与顺序

- 默认在工作簿旁维护一份累计 Markdown：`<workbook-basename>.xlsx` 对应 `<workbook-basename>.md`。
- case 小节按工作簿行号排列，不能按诊断时间、commit 顺序或测试文件名排列；必要时重排已有小节。
- 只有多个行共享同一根因和同一完整解决方案，或必须合并解释的参数化变体，才能归入同一个 case 小节。分组行必须提供“行号到 nodeid”映射表。
- 不相关 case 即使修改同一源码文件，也必须分开记录。
- 增量更新现有报告。保留正确的既有证据；新分析改变结论时，修订已过时的排序、编号、路径、状态或结论。
- 使用当前实际环境中的精确证据。不得把示例、建议、未应用 patch、installed-tree 验证副本或历史修复描述为已经应用到源码树的修改。
- 当前 case 因 guard、fallback、skip、禁用优化或 workaround 而通过时，分别记录历史原始失败、当前遏制状态和目标修复状态，不能把目标路径未执行写成已修复。

## 文档头必备内容

所有 case 小节之前，文档开头必须包含以下全局信息。

### 1. 标题与运行环境

标题使用 `# <workbook filename>.xlsx 分析`，然后记录：

- 环境激活命令（如有）；
- 仓库路径和 pytest 工作目录；
- Python 可执行文件与版本；
- 实际导入的 PyTorch 版本和 `torch.__file__`；
- HIP/ROCm、CUDA 等 accelerator/runtime 版本；
- 相关 GPU/device 型号；
- 编译仓、代码记录仓和安装验证仓；
- 测试源码实际来自哪个 checkout；
- 工作簿路径；报告只覆盖部分 sheet 时写出范围。

未知值写 `未确认`，并附取得该值所需命令，不得猜测。三类仓库必须分别记录，即使路径相同也要写明“编译仓 = 代码记录仓”等关系。测试源码 checkout 与实际导入 runtime package 必须分开，因为 pytest 可能从仓库读取测试，却加载已安装的 Torch。

推荐使用以下表格记录三类仓库：

| 仓库角色 | 路径 | 用途 | branch/HEAD 或版本 | dirty/验证状态 | 是否可提交 |
| --- | --- | --- | --- | --- | --- |
| 编译仓 | `<compile-repo>` | 构建源码、生成 build 产物、运行依赖编译结果的测试 | `<branch>/<HEAD>` | `<状态>` | `否；除非与代码记录仓相同` |
| 代码记录仓 | `<code-record-repo>` | 保存 case 修改、生成 Git diff、commit 和 push | `<branch>/<HEAD>` | `<状态>` | `是，唯一提交来源` |
| 安装验证仓 | `<Path(torch.__file__).resolve().parent>` | pytest 实际导入的 runtime 验证 | `<torch version>` | `<validation-only 状态>` | `否；允许保留有效验证修改` |

### 2. 当前仓库状态

记录一份简洁快照：

- 仓库路径；
- 编译仓、代码记录仓、安装验证仓的路径和角色关系；
- 当前 branch 和完整或缩写 HEAD；
- 有帮助时记录 HEAD subject；
- user fork、internal main、official PyTorch remote 的实际映射；
- 用于对比的 target/base branch 或 release；
- dirty worktree 状态，以及哪些修改属于本次分析；
- 编译仓中的临时同步 patch、build 产物，以及安装验证仓中仅用于验证的修改（如有），并明确它们不在代码记录仓 Git 中、不能提交；安装验证仓中验证有效的修改可以保留，用于用户后续复测。

仓库快照附近必须写代码提交状态。没有源码修改时写 `代码提交状态：无待提交修改`。存在建议、已应用、已提交或已推送修改时，准确说明状态和计划/实际目标分支。

只要存在代码修改，就在文档顶部放一张权威“逻辑修改/提交表”，并把它作为全文编号的唯一事实来源：

| 顺序 | 工作簿行 | Case/根因 | 源码文件或 hunk | 状态 |
| --- | --- | --- | --- | --- |
| 1 | `<rows>` | `<short diagnosis>` | `<paths and focused change>` | `<已应用未提交 / 已提交 HASH / 未应用建议 / 无修改>` |

只对真正构成逻辑 commit 的修改编号。可选或未应用 follow-up 在实际采纳前不编号。commit 或 push 完成后，用真实 hash、branch、target branch 和 push/MR 状态更新该表，并与每个 case 的 `提交建议` 保持一致。

### 3. 适用时的全局说明

只有确实影响多个 case 时才增加简短全局说明，例如：

- 编译仓构建策略和安装验证仓验证策略；
- 使用的官方诊断路线；
- 工作簿错误日志的限制；
- 共享 runner 或环境 warning；
- 已应用、未应用建议和无 diff 方案之间的区别。

不要在文档头重复每个 case 的分析。

## case 固定结构

每个 case 或同类 case group 使用一个 `##` 标题，并严格按顺序保留以下五个 `###` 小节。

`##` 标题之后立即写：

```text
工作簿位置：工作表 `<准确 sheet 名>`，第 <单行、范围或行号列表> 行。
```

使用工作簿显示行号。分组 case 再增加紧凑表格，至少记录行号、精确 pytest nodeid、相关 variant/input、原始结果和最终处理结果。已知准确 sheet 名时，不能只写“sheet4”；可以同时记录序号和准确名称。

### 1. 报错信息

包含：

- 工作簿原始错误、状态、耗时或 raw log 摘要；
- 精确复现命令和简洁结果；
- 当前复现是否与工作簿一致；
- 能区分失败的 sample index、dtype、device、shape、backend、生成测试身份或调用点；
- 相关 warning，但要与真正失败条件分开。
- 适用时区分历史失败、当前遏制和目标修复；只具备静态历史证据时明确标记，不能写成当前直接复现。

工作簿没有错误详情或 case 当前通过时，直接说明，不能借用相邻行错误或虚构失败。证据没有建立关联时，要区分 runner 级 STALL/TIMEOUT 和测试内 Python/C++ assertion。

### 2. 测试目的与错误分析

从测试源码向调用链展开说明：

- test/template 和 parameterization 定义位置；
- 相关时说明具体 nodeid 的生成方式；
- input/sample 构造和关键 shape/dtype/device/backend；
- assertion 保护的行为或 contract；
- 相关 forward/backward、dispatcher、compiler、generated code 或 runtime 调用链；
- 精确失败层和根因；
- 相邻 warning 或表面相似 case 为何是或不是同一问题；
- 先写官方 PyTorch `main`/release/PR/issue/commit 结论，官方证据不足再写内部 upstream；
- 最终分类，如 runtime defect、测试预期漂移、数值/reference 不一致、环境/数据问题、能力缺口或 flaky。
- candidate/dispatch/autotune 问题的 eligibility、外层 guard、目标候选是否注册/生成/执行，以及自然 PASS 是否来自其他 backend 或 fallback。

每个结论都应连接到复现、源码、历史或 upstream 证据。有链接或 commit hash 时准确记录。不确定性应作为残余不确定性明确写出，不能把假设改写成事实。

### 3. 解决方法

开头必须用以下一种状态明确标记代码修改情况：

- `已应用源码修改`；
- `已应用 test-only 修改`；
- `未应用的可选方案`；
- `当前基线已修复，无新增 diff`；
- `仅诊断，未修改`。

然后包含：

- 代码记录仓中修改的准确源码文件；
- 每个已应用逻辑修改的聚焦 unified diff（必须从代码记录仓的 `git diff`、`git diff --cached` 或 `git show` 生成）；
- 若为编译验证，编译仓同步了哪些文件、基线是什么、运行了什么构建命令；
- changed field、branch、condition、metadata 或 assertion 如何解决根因；
- 方案为何保留原测试目的；
- 受影响和不受影响的 platform/dtype/shape/test；
- 采用、适配或有意不采用官方方案的理由；
- 要求保留性能优化时，说明方案如何恢复正确性和原性能目标；删除候选、广泛 fallback 或硬编码失败 shape 只能标为 workaround；
- 若同步修改编译仓或安装验证仓仅作验证，必须单独标记，并从代码记录仓待提交 diff 排除。安装验证仓中已验证有效的修改可以保留，但必须标记为“保留的 validation-only 修改”；三者 patch 不一致时，不能称作同一修复。

无修改 case 要明确写“当前没有待提交源码 diff”以及原因。建议方案的 diff 必须标为 `未应用`，后续测试结果不能称为“修复后验证”。

### 4. 修改后的测试结果

记录：

- 准确激活命令和测试命令；
- 精确 case 结果与简洁 pytest summary；
- 相邻/参数化/共享逻辑的 regression 覆盖；
- `py_compile`、`git diff --check` 等静态检查；
- 测试源码来自哪个仓库、编译产物来自哪个编译仓、实际 runtime 来自哪个安装验证仓；
- 编译命令、安装/同步命令及其结果（如有）；
- 候选路径敏感问题的强制/观测目标 candidate、非法适用域、base/fallback 和自然选择证据；
- 性能敏感正确性修复的同环境 base/优化对照、首次编译开销和单候选资源淘汰信息；
- 未运行的测试和准确 blocker；
- 残余风险，以及已完成测试不能证明什么。

无代码变化 case 应称为“当前基线验证”，不能暗示测试了某项修改。skip/xfail 要明确结果是 `SKIPPED`、`XFAIL` 还是真正 `PASS`，并解释该处理为何正确。

### 5. 提交建议

即使用户尚未要求 commit，也要写清审查边界：

- 是否需要提交；
- 来自全局表的逻辑提交顺序；
- 该 commit 覆盖的 case 行和根因；
- 应 stage 的文件与准确 hunk；
- 必须保持 unstaged 的文件/hunk；
- 适用时给出 title 和 Why/What/Impact body；
- 与该 commit 对应的验证证据；
- 当前状态：uncommitted、committed hash、pushed branch 或 MR source/target。

当前通过且无修改的 case 写 `无需提交`。runtime 修复与其聚焦 regression test 放在一起；独立 test-only 修复即使修改同一文件也应拆开。只在有帮助或用户要求时给具体 stage/commit 命令；命令必须符合 `commit_workflow.md` 和当前仓库惯例。

## 代码 diff 要求

- 已应用 diff 必须由 Git 生成（`git diff`、`git diff --cached` 或 `git show`），不能凭记忆重建。
- 使用仓库相对路径和 unified `diff --git` block，保留足以定位 function、class 或 OpInfo 的上下文。
- diff 聚焦当前 case 的逻辑修改，排除无关 dirty hunk、generated file、test log、工作簿/报告和 installed-package 验证副本。
- 长 runtime 修复需要缩短时，标为 `精简 diff（省略未改上下文）`，但保留所有有语义的 changed field/branch；不能用省略号隐藏待分析修复的一部分。
- 每个非简单 diff 后必须解释修改前/后的状态和与失败的因果关系；只有 diff 没有分析不完整。
- 历史或官方 diff 不能冒充本地已应用 diff，必须准确标明来源 commit 和状态。
- commit 后 worktree 不再含 patch 时，用 `git show <hash>` 更新 diff 和状态。

## 提交信息要求

- 全局逻辑修改表是序号的唯一权威来源。
- 插入、删除、重新分组或调整顺序后，更新所有 case 引用。稳定行号、case 名或 commit hash 更清晰时，避免“第三个”等易失效序数措辞。
- commit 前说明建议边界并标记 `待提交`。
- commit 后用真实 hash/subject 替换建议状态，并核对实际提交文件符合记录边界。
- push 后只记录实际推送的 branch/remote；仅有创建链接不能声称 MR 已存在。
- 可选未来 patch 在实际采用前不进入已应用编号序列。

## 一致性检查

交付报告前逐项确认：

1. case 小节按工作簿行号排序。
2. 每个 case 开头都有准确工作表和行号。
3. 每个 case 严格包含五个固定小节，顺序正确。
4. 已应用/未应用/无 diff 的措辞与实际 Git 状态一致。
5. 每项已应用代码修改都有聚焦 diff 和因果分析。
6. 验证结果对应第 3 节描述的同一代码状态。
7. 全局提交序号、逐 case 序号、hash、branch 和提交状态全文一致。
8. 相似 case 只有根因和方案一致时才分组，否则明确区别。
9. Markdown code fence 成对、table 可渲染、link 指向目标源码，path 可移植或明确标为特定环境证据。
10. 无关用户修改、编译仓临时 patch/build 产物、installed-runtime 副本、工作簿、报告或 cache 没有被描述成代码记录仓待提交修改。
11. 历史失败、当前遏制和目标修复没有混写；要求保留性能时，目标 candidate 和性能证据均已记录。

## 可移植模板

使用以下骨架并补充证据。没有全局说明时可省略可选项，但五个 case 小节绝不能省略。

````markdown
# <工作簿文件名>.xlsx 分析

运行环境：

```bash
<环境激活命令，如有>
cd <pytest 工作目录>
```

- Python：`<可执行文件>`（`<版本>`）
- 运行时 PyTorch：`<版本>`，`<torch.__file__>`
- 加速栈：`<HIP/ROCm 或 CUDA 版本>`
- GPU/设备：`<型号>`
- 测试源码：`<仓库/测试路径>`
- 工作簿范围：`<工作簿路径；适用时写选定 sheet>`

仓库角色：

| 仓库角色 | 路径 | 用途 | branch/HEAD 或版本 | dirty/验证状态 | 是否可提交 |
| --- | --- | --- | --- | --- | --- |
| 编译仓 | `<compile-repo>` | 构建和运行测试 | `<branch>/<HEAD>` | `<状态>` | `否；除非与代码记录仓相同` |
| 代码记录仓 | `<code-record-repo>` | 保存 diff、commit 和 push | `<branch>/<HEAD>` | `<状态>` | `是，唯一提交来源` |
| 安装验证仓 | `<torch.__file__ 所在目录>` | 实际导入 runtime 验证 | `<torch version>` | `<validation-only 状态>` | `否；允许保留有效验证修改` |

当前仓库状态：

```text
compile-repo: <路径、branch、HEAD>
code-record-repo: <路径、branch、HEAD>
validation-repo: <torch.__file__ 所在目录和版本>
target/base: <remote 角色和分支>
working tree: <三类仓库各自 clean 或范围明确的 dirty changes>
remotes: <已映射 fork/internal/official 角色>
代码提交状态: <无待提交修改 / 计划修改 / 已应用未提交 / 已提交 / 已推送；目标分支>
```

<编译命令、编译产物来源、安装/同步命令，以及可保留的 validation-only 修改说明，如有>

| 顺序 | 工作簿行 | Case/根因 | 源码文件或 hunk | 状态 |
| --- | --- | --- | --- | --- |
| 1 | `<行号>` | `<根因>` | `<文件/修改>` | `<状态/hash>` |

## <case 或同类 case group 名>

工作簿位置：工作表 `<准确 sheet 名>`，第 `<行号>` 行。

<可选：行号/nodeid 映射表>

### 1. 报错信息

<工作簿证据、复现命令/结果、匹配状态；适用时写历史失败/当前遏制/目标修复>

### 2. 测试目的与错误分析

<测试源码、生成/调用链、目的、证据、根因、官方/内部检索结论；适用时写 candidate eligibility/执行路径>

### 3. 解决方法

状态：`<已应用源码修改 / 已应用 test-only 修改 / 未应用的可选方案 / 当前基线已修复，无新增 diff / 仅诊断，未修改>`

修改文件（代码记录仓）：`<仓库相对路径或无>`

```diff
diff --git a/<path> b/<path>
<聚焦的实际 diff，或明确标记的未应用建议 diff>
```

<修改前后行为和因果分析；影响范围与备选方案；如需编译，说明编译仓同步 patch；如需安装包验证，说明安装验证仓同步 patch>

### 4. 修改后的测试结果

```bash
<准确验证命令>
```

```text
<准确简洁结果>
```

<相邻检查、静态检查、runtime 来源、残余风险；适用时写强制候选、非法适用域、fallback、自然选择和性能证据>

### 5. 提交建议

<提交边界/顺序/状态、title/body、stage 与排除的 hunk、已完成时写 hash/branch>
````
