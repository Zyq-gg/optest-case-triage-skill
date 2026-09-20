---
name: optest-case-triage
description: "用于分析 PyTorch optest/pytest case 或实际使用中遇到的问题，也可在分析完成后依据权威 Markdown 安全回填 CSV。接受 Excel 行、pytest nodeid、问题描述、日志、脚本、命令、模型运行现象或问题现场连接方式；覆盖环境采集、复现、归属判断、官方与上游检索、根因分析、最小修改、分层验证和结构化文档，仅在用户明确要求时提交或推送。"
---

# PyTorch Optest 与问题分析

## 概述

本 skill 有三个相互独立的工作模式：

1. **Optest/pytest case 分析**：从工作簿的一行或 pytest nodeid 出发，完成复现、诊断、修改、验证和工作簿 Markdown 记录。
2. **PyTorch 使用问题分析**：从问题描述、日志、脚本、命令、运行现象或问题现场出发，建立问题身份、复现、判断归属、修复、验证并生成独立问题报告。
3. **分析后 CSV 回填**：以已经完成的工作簿 Markdown 报告为权威来源，安全回填用户 CSV 中的四个汇总字段。

先按输入自动选择模式。不要把 CSV 回填与 case/问题复现、代码修改混在同一个流程中；不要给一般使用问题强加工作簿行号或 pytest 结构。

适用请求包括：

- 分析 optest Excel 中的某个具体 case；
- 复现 PyTorch 单元测试失败并解释根因；
- 结合工作簿历史记录和当前源码判断问题状态；
- 检索 PyTorch 官方或内部上游是否已有修复；
- 尝试最小化源码或测试修改并验证；
- 生成或完善逐 case 的 Markdown 分析文档；
- 分析使用 PyTorch 时的异常、hang、数值、性能、内存、安装、编译、backend、distributed 或第三方扩展问题；
- 在当前环境或用户提供的远程问题现场复现，也可基于日志完成明确标记的静态诊断；
- 依据现有 Markdown 和任意辅助 CSV 列回填 `测试目的`、`解决方案`、`最终状态`、`遗留原因`；
- 在用户明确要求后，将已验证修复拆成可审查的提交并推送到用户 fork。

不要用本 skill 批量提取原始日志、创建新的失败工作簿或标记新增 Excel 行；这些任务属于 `torch-optest-log-xlsx-skill`。

典型输入：

- optest Excel 工作簿，以及 op 名或 `(py name, class, op name)`；
- 不涉及工作簿时，可直接提供 pytest nodeid；
- PyTorch 问题描述，以及可选的日志、复现命令、脚本、用户项目、预期行为或问题现场连接方式；
- 文档回填模式下，提供已完成的 Markdown 报告和待汇总 CSV。

典型输出：

- 有证据支撑的具体诊断；
- 精确复现命令与结果；
- 查到的官方/上游修复证据；
- 尝试或应用的本地修改；
- 验证结果与残余风险；
- 按工作簿行号排列、包含统一文档头和五节 case 记录的累计 Markdown 报告；
- 或包含问题身份、现场、归属、四类仓库、五节分析、验证和提交边界的 PyTorch 使用问题报告；
- 或在独立文档模式下，四个汇总字段来自 Markdown、其余字段保持不变且结构验证通过的 CSV。

## 可移植性和环境规则

每次进行 optest case 或 PyTorch 使用问题分析，首先完整阅读 [references/portable_setup.md](references/portable_setup.md)。

- `<skill-dir>` 表示本 `SKILL.md` 所在目录；脚本、依赖声明和参考文档都从该目录解析。
- 使用用户指定的问题现场/用户项目、编译仓、代码记录仓、Python 环境、工作簿和输出路径。需要 PyTorch 源码时明确区分编译仓、代码记录仓和安装验证仓；三者相同时仍分别记录角色。不涉及源码时允许编译仓和代码记录仓为 `未使用/不适用`。只有验证后才能采用当前目录或当前环境，不猜测固定主机路径和激活脚本。详细规则见 [references/portable_setup.md](references/portable_setup.md)。
- 三仓默认数据流是：**代码记录仓提供全部源码修改和 test 代码，安装验证仓提供 pytest 实际加载的 `torch` runtime；编译仓只承接必须编译的源码镜像**。test-only 修改不得同步到编译仓；无需编译的 Python runtime 修改从代码记录仓同步到安装验证仓验证，也不得触碰编译仓。除非用户明确要求执行 PyTorch 源码编译，否则不得运行构建命令。
- 将 `origin`、`upstream`、`official` 视为逻辑角色，按 URL 或用户说明映射；只 fetch 已配置 remote，缺少可选参考 remote 时继续完成可执行的本地分析。
- fork 开发分支（例如 `2.9.1-dev-xxx`）通常对应内部基线 `2.9.1-dev`；除非用户另有指定。内部版本再映射到官方发布线（例如 `release/2.9`）判断覆盖情况。
- 官方检索顺序是 `main`、较新的 release、目标 release。没有本地 official remote 时，使用本 skill 的官方技能指引和实时 GitHub 链接。
- CSV 文档工作流不要求 PyTorch checkout 或运行时；路径和规则直接按 [references/csv_report_backfill.md](references/csv_report_backfill.md) 处理。

除非用户明确要求，不得提交、推送或向任何 remote 发起 MR/PR。

## 能力与边界

本 skill 可以：

- 定位工作簿行，处理包含匹配和歧义候选；
- 读取 `错误结果`、`详细分析`、`测试目的`、`历史版本分析`、`新增标记` 等有效列；
- 在正确环境和工作仓库中复现失败；
- 从问题描述、日志或现场建立可追溯的问题身份，并尽量自动发现环境信息；
- 判断问题属于使用/配置、环境安装、用户项目、第三方扩展、PyTorch runtime/compiler/backend、数值、性能、内存、distributed 还是数据/模型；
- 将现象归类为仍可复现、已修复、flaky、仅环境相关或日志不匹配；
- 检查本地源码、测试以及 `upstream/*`、`official/*` 的历史；
- 在需要且网络可用时检索官方 PyTorch issue、PR、tag 和源码；
- 按问题类型调用匹配的官方 PyTorch 诊断方法；
- 移植官方修复，或在没有适用官方修复时提出最小本地方案；
- 验证精确 case 以及受共享逻辑影响的相邻 case；
- 输出包含环境、仓库、提交状态、diff、验证和残余风险的统一 Markdown 报告；
- 用户明确授权后，按根因拆分提交并准备 MR/PR；
- 以 Markdown 为权威证据回填 CSV 四个汇总字段。

必须遵守：

- “分析”“修改”“验证”不等于授权 commit、push 或创建 MR/PR，这些是独立动作。
- 官方 PyTorch skill 只提供诊断方法，不自动授予修改 GitHub issue、label、comment、branch、commit 或 remote 的权限。
- 不用大范围 skip、全局放宽容差或无关重构换取测试通过。
- 工作簿记录只是假设来源，不是结论证据。
- 不覆盖用户已有修改；dirty worktree 必须先检查并与现有改动共存。
- 用户项目/问题现场与 PyTorch 代码记录仓是不同边界；未经用户要求，不修改用户项目。需要修改时单独生成 diff、验证和提交。
- 运行用户脚本前做与风险匹配的轻量检查；不因安全检查制造繁琐流程，但不得静默执行下载、安装、提权、危险反序列化、破坏性写入或超大长时任务。
- 在改变测试语义或设计本地 workaround 前，优先检查官方 `main`、release、commit、PR 和 issue。
- 选择最小且有证据的补丁；移植测试预期时必须解释语义为何成立。
- 当前环境因 guard、fallback、skip、禁用优化或 workaround 而通过时，区分历史原始失败、当前遏制状态和目标修复状态；不能把路径未执行写成根因已修复。
- compiler/autotune/dispatch 等候选路径敏感问题必须证明目标路径真实注册并执行；要求保留性能时同时验证正确性、fallback、自然选择和同环境性能。
- CSV 回填不得硬编码辅助列字母（例如 L）；按表头和内容发现列，冲突时以当前 Markdown 为准。

## 模式路由

按最强输入信号自动选择，不要求用户手工选择：

```text
XLSX 行、sheet/op 身份或 pytest nodeid
    → Optest/pytest case 分析

问题描述、日志、命令、脚本、模型运行现象或问题现场
    → PyTorch 使用问题分析

已完成工作簿 Markdown + 待回填 CSV
    → CSV 回填
```

输入同时包含 pytest 和用户工作负载时，以用户目标为准：用户要处理工作簿行则走 case 模式；用户要解决真实工作负载则走使用问题模式，并把 pytest 作为 regression 证据。

## 模式一：Optest/pytest case 分析

### 1. 读取工作簿行

运行测试前先找到目标行。优先使用完整测试身份字段。常见前三列是 `py name`、`class`、`op name`；列名不同时，仍将前三列视为 case 身份。

必要时使用：

```bash
python3 <skill-dir>/scripts/find_case_in_xlsx.py \
  --xlsx <workbook.xlsx> \
  --op-name test_name_or_substring
```

记录文件/模块、类、测试/op 三个身份字段。其余列不能写死名称；读取对当前判断有用的目的、方案、状态、复测状态、备注、遗留原因、错误信息、历史分析和本地分析列。

工作簿内容用于形成初始假设，不得直接当成证明。若匹配多行，列出候选；只有 sheet、完整类名或精确 op 名等信息足以消除歧义时才选择。

### 2. 复现 case

使用**代码记录仓中的 test 文件**运行精确 pytest，同时确保 `torch` 从安装验证仓导入。不要从编译仓读取或同步测试文件。优先从代码记录仓的 `test/` 目录运行，避免仓库根目录的源码包遮蔽已安装 runtime：

```bash
<用户提供的环境激活命令，如有>
cd <code-record-repo>/test
python -c 'from pathlib import Path; import pytest, torch; print(Path(torch.__file__).resolve().parent); raise SystemExit(pytest.main(["-vs", "<path-relative-to-test-dir>::CLASS_NAME::OP_NAME"]))'
```

上面的 wrapper 在 pytest 改变 import path 前先导入并打印 `torch`，确保测试进程复用同一个安装 runtime。确认路径等于已记录的安装验证仓。若实际导入代码记录仓或编译仓中的 `torch`，先修正工作目录、`PYTHONPATH` 或 editable-install 影响；在 runtime 来源正确前，不得把结果当作权威复现或修复后验证。

pytest 路径可能因工作目录带或不带 `test/` 前缀。在认定无法收集前先规范这两种形式：

```text
test/dynamo/test_activation_checkpointing.py
dynamo/test_activation_checkpointing.py
```

参数化收集需要时可使用：

```bash
pytest -vs PY_NAME -k OP_NAME
```

记录通过/失败、简洁异常、耗时、生成代码路径、warning、编译/链接信息，以及当前错误是否与工作簿一致。

复现时阅读代码记录仓中的测试函数和相关 helper，明确测试目的。后续不得通过切换 backend、dtype、skip 条件、预期文本或断言，使测试虽然通过却不再测试原语义。

test-only 修改始终只落在代码记录仓，并直接使用该仓 test 文件验证，不得为验证 test 修改而改动编译仓。无需编译的 Python runtime 修改也只在代码记录仓记录，再将同一文件同步到安装验证仓供 pytest 加载。只有 C/C++、生成绑定或其他必须重新编译才生效的源码修改，才允许把相同 patch 临时同步到编译仓；即便如此，没有用户明确要求也不得执行 PyTorch 源码构建。安装验证仓中验证有效的 runtime 修改默认保留，不自动回退，以便用户后续复测；它仍然不能进入代码记录仓 commit。

若用户提供环境激活命令，使用该命令。否则保留当前环境，并记录 `sys.executable`、`torch.__version__`、`torch.__file__`。

慢速或疑似 flaky 的测试只在能显著提升结论可信度时重跑。重跑通过时谨慎归类：

- `已修复/当前通过`：当前代码无法复现工作簿失败；
- `flaky/环境相关`：失败与时序、资源或环境有关；
- `日志不匹配`：行记录很可能来自另一构建或配置。

### 3. 优先检索官方，再检查内部上游

设计本地修复前，必须先找官方方案。若官方 commit、PR、issue 或 release 变更能解释失败，优先移植或最小化适配；官方证据不足时，再把内部 `upstream` 作为主要参考。

先检查代码记录仓，并同步确认编译仓和安装验证仓：

```bash
git -C <code-record-repo> status --short --branch
git -C <code-record-repo> remote -v
git -C <code-record-repo> branch -vv
git -C <code-record-repo> log --oneline --decorate --all -- PY_NAME
git -C <compile-repo> status --short --branch
git -C <compile-repo> rev-parse HEAD
python -c "from pathlib import Path; import torch; print(Path(torch.__file__).resolve().parent)"
```

按 `portable_setup.md` 映射 fork、内部主线和官方 PyTorch，只 fetch 已配置 remote：

```bash
git -C <code-record-repo> fetch <configured remote> --prune
git -C <code-record-repo> rev-parse --short HEAD
git -C <code-record-repo> rev-parse --short <remote>/<branch>
```

官方检索顺序：

1. 在官方 `main` 按测试名、文件、错误文本、相关函数或行为检索。
2. 检索已获取的较新官方 release；修复可能只存在于较高版本。
3. 检查目标官方 release/tag，例如 `official/release/2.9`、`v2.9.1`、相关 rc tag。
4. 检索官方 commit、PR 和 issue；利用 git log、源码注释、工作簿或错误文本中的编号。
5. 仍无官方方向时，从新到旧检查内部 `upstream` 开发分支，最后再看目标基线。

每个非简单 case 都要记录：找到精确官方修复、相关官方修复，还是未找到相关官方修复。本地方案不同于官方方向时，必须解释原因。

不要为比较而 checkout 覆盖 dirty worktree，可使用：

```bash
git -C <code-record-repo> diff upstream/BASE_BRANCH...HEAD -- PY_NAME
git -C <code-record-repo> diff official/release/2.X..official/main -- PY_NAME
git -C <code-record-repo> diff official/release/2.X..official/release/NEWER_2.X -- PY_NAME
git -C <code-record-repo> diff upstream/BASE_BRANCH..upstream/NEWER_DEV_BRANCH -- PY_NAME
git -C <code-record-repo> show official/main:PY_NAME
git -C <code-record-repo> show upstream/BASE_BRANCH:PY_NAME
git -C <code-record-repo> show --stat --oneline COMMIT
git -C <code-record-repo> show --unified=80 COMMIT -- PY_NAME
```

remote 名只是示例，必须替换成实际映射；缺少可选 ref 只降低对比覆盖，不阻止本地复现和诊断。

已知候选 commit 时检查分支覆盖：

```bash
git -C <code-record-repo> branch -r --contains COMMIT
git -C <code-record-repo> merge-base --is-ancestor COMMIT official/main
git -C <code-record-repo> merge-base --is-ancestor COMMIT official/release/NEWER_2.X
git -C <code-record-repo> merge-base --is-ancestor COMMIT upstream/BASE_BRANCH
git -C <code-record-repo> rev-list --left-right --count upstream/BASE_BRANCH...COMMIT
git -C <code-record-repo> diff --stat upstream/BASE_BRANCH..COMMIT
git -C <code-record-repo> diff COMMIT^..COMMIT -- PY_NAME
```

候选提交的逻辑可复用不代表其旧分支可直接合并；分支落后、分叉或含无关差异时，从当前目标基线重新应用聚焦 hunk。

需要联网检索时，以官方 PyTorch 来源为先：

- `https://github.com/pytorch/pytorch/issues`
- `https://github.com/pytorch/pytorch/pulls`
- `main`、release tag 或 patch tag（例如 `v2.12.1`）的 raw source

搜索词包括 op/test 名、class 名、精确错误、相关文件/函数，以及本地历史发现的 issue/PR 编号。

结论分类：

- **找到官方修复**：能适用时移植或适配，记录 commit、PR/MR、issue 和 branch/tag 覆盖；
- **找到相关官方修复**：解释重叠点以及为何能或不能解决当前 case；
- **无官方修复但有内部 upstream 修复**：最小化采用，并明确它是内部/下游方案；
- **未找到官方修复**：基于证据继续设计最小本地修复。

### 4. 诊断根因

结合复现、工作簿历史、源码和官方检索证据。深入分析前完整阅读 [references/official_pytorch_skills.md](references/official_pytorch_skills.md)，选择匹配的官方诊断路线。official remote 或网络可用时，可只刷新当前问题需要的官方 skill；复现需要稳定时用固定 commit 链接，检查最新指导时用 `main`。

官方 skill 提供领域诊断方法；环境选择、dirty worktree、修改范围、验证、Markdown、commit 和 remote 操作仍由本 skill 约束。

常见根因类别：

- backend 能力缺口：HIP/ROCm/CUDA 路径缺少实现或 guard；
- 数值不一致：dtype、累加方式、算法或容差导致与 eager/reference 不同；
- compiler/codegen 缺陷：Inductor/Triton lowering、scheduler、template 或生成 kernel 错误；
- 测试预期漂移：上游行为、golden 文本或计数已变化；
- 环境/数据问题：依赖、下载、cache、网络、设备能力、构建或时限；
- flaky/时序：阈值对环境或负载过于绝对；
- distributed/runtime 配置：rank 数、process group、设备或算子路径不支持。

对选定类别说明支持证据，并指出什么证据能推翻该判断。

### 5. 尝试最小修改

只修改解决当前问题所需代码，并保留用户和已有本地变更。参考优先级：精确官方修复、相关官方方向、较新内部 upstream、目标分支本地推理。

所有 case 的代码修改都先且必须记录在代码记录仓，包括 test 文件、Python runtime 和需要编译的源码。修改 runtime 前，先确认测试环境实际导入的安装验证仓：

```bash
python -c "from pathlib import Path; import sys, torch; print(sys.executable); print(Path(torch.__file__).resolve().parent)"
```

按文件类型选择唯一允许的验证流：

- test-only：代码记录仓修改并从该仓运行 test；安装验证仓只提供原有 runtime；不修改编译仓。
- 无需编译的 Python runtime：代码记录仓记录修改，再同步到安装验证仓；从代码记录仓运行 test；不修改编译仓。
- 必须编译的源码：代码记录仓记录修改，再把相同源码 patch 临时同步到编译仓。只有用户明确要求源码编译时才构建，并把产物同步到安装验证仓验证；否则停在源码/static validation，明确记录“未编译、未做 runtime 验证”的 blocker。

每一步都记录基线和命令。文档中的待提交内容只记录代码记录仓源码树，编译仓临时源码镜像/build 产物和安装验证仓副本分别标为验证用途且绝不 stage。

推荐做法：

- 用语义断言代替任意 buffer 或常数；
- 用针对性 backend guard/fallback 代替广泛 skip；
- 限定 dtype/device/shape，而非改变全局行为；
- timing 测试尽量与实测 baseline 比较。

禁止做法：

- 不解释行为就修改预期值；
- 对无关平台做广泛 skip；
- 回退用户无关修改；
- 可以表达相对语义时仍使用无依据的固定阈值。

使用 `apply_patch` 手工编辑。若本地修复风险高或范围过大，停在诊断结论，说明更安全的后续方案。

### 6. 验证

用同一环境重跑精确失败 case。共享逻辑发生变化时，至少再跑一个相邻变体或窄范围 `-k` 集合。非简单 runtime 或测试框架修改还应执行 [references/official_pytorch_skills.md](references/official_pytorch_skills.md) 路由出的测试、兼容性和设计检查。

候选路径敏感问题不能只依赖自然 dispatch 的 PASS：强制或观测目标 candidate，验证不支持输入不会注册危险路径，并确认 base/fallback 仍可用。正确性修复同时承诺保留性能时，再用同环境 baseline、自然选择和同步重复测量证明没有通过撤掉优化规避。

记录精确命令和摘要，例如：

```text
PASSED [108.4338s]
1 passed in 113.57s
```

不能运行时说明阻碍和残余风险。验证等级：

- 仅精确 case：适合窄范围 test-only 修复；
- 精确 case 加相邻变体：适合参数化测试、dtype/device guard 或共享 helper；
- 小范围文件/class：适合 compiler/backend 公共逻辑；
- 未运行：仅在有明确 blocker 和风险说明时可接受。

### 7. 写 Markdown 记录

来自工作簿的 case 默认写到工作簿旁的同名 `.md`，例如 `report.xlsx` 对应 `report.md`。后续 case 追加到同一累计文档，不创建逐 case 文件，除非用户明确要求。

没有工作簿或用户要求独立文件时，使用用户提供路径或当前任务目录。

写入或修订工作簿报告前，必须完整阅读 [references/markdown_report.md](references/markdown_report.md)，并以其中的文档契约和可移植模板为准。核心要求：

- 文档开头记录编译仓、代码记录仓、安装验证仓三类角色的路径、branch/HEAD、dirty 状态和用途；同时记录实际导入 runtime、remote/base、仅验证用副本，以及代码提交和目标分支状态。有代码修改时只保留一张权威逻辑提交表；没有待提交源码也必须明确写出。
- case 按工作簿行号排序。每个 case/group 开头写准确 sheet 和行号/范围/列表；参数化分组增加行号到 nodeid 的映射表。
- 每个 case 严格保留五节且顺序固定：`报错信息`、`测试目的与错误分析`、`解决方法`、`修改后的测试结果`、`提交建议`。
- `解决方法` 区分已应用源码修改、已应用 test-only 修改、未应用建议、当前基线无 diff、仅诊断。每项已应用修改都提供由 Git 生成的聚焦 unified diff，并解释修改前后行为和因果关系。
- 代码记录仓 diff 是唯一的 applied/submission diff；编译仓同步 patch、build 产物和安装验证仓镜像必须单独列为验证副本，不得把它们或官方、历史、建议 diff 冒充本地已应用修改。
- `修改后的测试结果` 记录完整命令、结果、相邻覆盖、静态检查、runtime 来源、blocker 和残余风险；基线通过不能写成修复后通过。
- `提交建议` 与全局表保持同一逻辑分组和顺序，写明 stage/排除的文件或 hunk、提交状态/hash/branch；无代码变化写 `无需提交`。
- 交付前核对行号顺序、五节完整性、代码围栏、diff/status、验证状态和全局/逐 case 提交编号。

检查过官方 PR/issue/source 时写入第 2 节；未找到官方修复也要明确说明。记录使用的官方诊断 skill、来源 ref/commit，以及因与本流程冲突而未采用的指导。

### 8. 仅在明确要求时提交和交付

只有用户明确要求 commit、push 或准备 MR/PR 时才进入此阶段。操作前必须完整阅读 [references/commit_workflow.md](references/commit_workflow.md)，按其规则选择分支、按逻辑拆分提交、控制 staging、设置作者和消息、验证、只向 fork 推送并完成交付说明。

固定原则：

- 只提交代码记录仓中的源码树修改；不 stage 编译仓临时 patch/build 产物、安装验证仓副本或仓库外分析文档。若编译仓和代码记录仓是同一路径，仍按代码记录仓的 Git 边界提交。
- 只有共享同一根因和同一完整修复的 case 才进入一个 commit。互不相关的 runtime、backend、测试预期和基础设施修改必须拆分。
- 只允许向 `origin` push，且 push 必须由用户明确要求。

## 模式二：PyTorch 使用问题分析

输入是问题描述、日志、脚本、命令、模型运行现象或问题现场时，完整阅读 [references/problem_triage.md](references/problem_triage.md)，按其中路线完成：

1. 从已有材料自动建立问题身份，不要求用户先填写固定表单；预期行为是可选输入，缺失时可依据可信 contract 推断并标记。
2. 优先在用户提供的直接环境复现；用户给出连接方式时进入问题现场；只有日志时做明确标记的静态诊断。
3. 记录用户项目/问题现场，并按需记录 PyTorch 编译仓、代码记录仓和安装验证仓；PyTorch 源码不涉及时允许写 `未使用/不适用`。
4. 对下载、安装、危险反序列化、破坏性写入和超大长时任务做轻量安全检查；普通只读复现直接推进。
5. 复现并保持错误签名或稳定现象，区分历史原始失败、当前遏制状态和目标修复状态；自动判断问题属于使用/配置、环境、用户项目、第三方、PyTorch runtime/compiler/backend、数值、性能、内存、distributed 还是数据/模型。
6. 按领域路由并优先检索官方/版本历史，再自动选择配置、项目、安装、第三方、PyTorch、unsupported、workaround 或仅诊断方案；只有重大语义/权限取舍才让用户选择。
7. 分层验证原始/等价复现的预期行为；PyTorch 源码修复再运行 regression 和相邻测试。候选路径敏感问题补充目标路径、非法适用域、fallback 和自然选择证据；性能目标补充同环境对照。错误消失但语义未验证不算完整修复。

用户项目与 PyTorch 代码记录仓属于独立修改和提交边界。所有 PyTorch applied diff 和 test 代码来自代码记录仓；无需编译的 Python runtime 只同步到安装验证仓，必须编译的源码才可同步到编译仓。除非用户明确要求，不执行 PyTorch 源码编译。安装验证仓中验证有效的修改默认保留供用户复测，但不 stage/commit。

创建报告前完整阅读 [references/problem_report.md](references/problem_report.md)。一般问题报告不使用工作簿行号，固定包含：`问题现象与报错信息`、`预期行为与错误分析`、`解决方法`、`验证结果`、`提交建议`。默认写到用户指定路径、日志旁或当前任务目录的 `pytorch_problem_<short-name>.md`。

环境信息可安全采集：

```bash
python3 <skill-dir>/scripts/collect_pytorch_env.py
python3 <skill-dir>/scripts/collect_pytorch_env.py --json
```

只有用户明确要求 commit、push 或 MR/PR 时才读取 `commit_workflow.md`。同时修改用户项目和 PyTorch 时，分别提交、分别验证，不创建跨仓库 commit。

## 模式三：由 Markdown 回填 CSV

这是分析完成后的独立文档任务，不是单 case 流程的第 9 步。仅当 Markdown 已完成且用户要求更新 CSV 汇总字段时使用。

完整阅读 [references/csv_report_backfill.md](references/csv_report_backfill.md)。它规定：

- Markdown 优先于 CSV 的证据顺序；
- 不依赖列字母或位置的辅助列动态发现；
- 精确 case 匹配和歧义处理；
- `测试目的`、`解决方案`、`最终状态`、`遗留原因` 的简洁语义和状态词；
- 可审查 JSON update plan；
- 保留 BOM、case 身份、非目标列、行序和逻辑行数的结构验证。

先形成语义 update plan，再运行 `scripts/backfill_triage_csv.py`。该 helper 不解释 Markdown，只负责防止把正确分析写错行或改写无关 CSV 数据。

## 辅助脚本

`scripts/collect_pytorch_env.py` 安全读取 Python、PyTorch、设备和实际安装验证仓信息，不收集完整环境变量或凭据。它用于使用问题模式，也可辅助 optest 环境记录。

`scripts/verify_runtime_sync.py` 只读比较代码记录仓源码文件与安装验证仓镜像的大小和 SHA256；退出码 `0/1/2` 分别表示一致、不一致、读取失败。用它证明安装环境验证的是同一份 runtime patch，不能用它替代构建产物逻辑等价分析。

`scripts/find_case_in_xlsx.py` 用于定位工作簿行，并输出匹配行的所有非空列：

```bash
python3 <skill-dir>/scripts/find_case_in_xlsx.py \
  --xlsx <workbook.xlsx> \
  --op-name test_max_min_bool_cpu

python3 <skill-dir>/scripts/find_case_in_xlsx.py \
  --xlsx <workbook.xlsx> \
  --py-name test/test_ops.py \
  --class-name TestCommonCPU \
  --op-name test_max_min_bool_cpu \
  --exact \
  --json
```

供其他脚本消费结果时使用 `--json`。

CSV 文档流程：

```bash
python3 <skill-dir>/scripts/backfill_triage_csv.py \
  --csv <input.csv> \
  --plan <updates.json> \
  --dry-run
```

## 与 torch-optest-log-xlsx 的关系

用户要求批量解析日志、创建三列/六列 Excel、标记新增 case 时，先使用 `torch-optest-log-xlsx-skill`。

用户选定具体行后，再使用本 skill 完成精确复现、源码与官方/上游检查、最小修改、验证和 Markdown 记录。

分析全部完成后，若用户需要把 Markdown 结论汇总到四个 CSV 字段，再使用本 skill 的独立 CSV 回填流程；它消费已有分析，不替代批量失败提取或逐 case 验证。

## 典型判断示例

### 实际使用问题

用户报告 `torch.compile` 模型 crash 时，先在问题现场保留原始模式复现，对照 eager/compiled 并路由 PT2；若根因是项目中不受支持的动态 Python 行为，优先调整用户项目或明确 graph break，不强行修改 PyTorch。若确认是 Inductor 缺陷，才在代码记录仓修复；Python runtime 修改直接同步安装验证仓，只有必须编译的源码才同步编译仓，且构建需要用户明确要求。随后使用代码记录仓 regression test 和安装验证仓 runtime 验证。涉及 autotune/template 优化时，强制目标 candidate 验证其正确性，用不满足适用域的输入验证 guard，检查普通 fallback 保留，再运行自然 autotune 和同环境性能对照；当前版本若仅因删除 candidate 而通过，应标为优化回退后的遏制状态。

### Timing 测试

对 `test_forkserver_perf`，固定 `+5` 阈值虽可能通过，但弱于把并行耗时和实测串行 baseline 比较：

```python
serial_elapsed = time.perf_counter() - start
self.assertGreaterEqual(serial_elapsed, Expensive.SLEEP_SECS * nprocs)

parallel_elapsed = time.perf_counter() - start
self.assertLess(parallel_elapsed, serial_elapsed / 2)
```

这保留了“并行 forkserver 启动应显著快于非并行启动”的测试目的，同时降低环境导入开销造成的误报。

### 已有官方修复

对 `test_max_min_bool_cpu`、`test_max_min_bool_cuda` 等 case，先在 `official/*` 和 `upstream/*` 历史中查找相同变化。若较新官方 commit 已调整 bool max/min 行为或测试预期，移植最小补丁，不另造方案；再验证 CPU/CUDA 变体，并在 Markdown 中记录来源。

### 环境或数据问题

`test_module_backcompat` 可能下载并加载旧版 `linear.pt`。若复现得到 `EOFError: Ran out of input`，先检查下载/cache 文件是否为空或损坏，不要直接修改 PyTorch serialization。源码逻辑正常时归类为环境/数据问题。

### Backend 能力缺口

FP8 或 scaled matmul case 需要同时检查 Python 测试预期、`ScaledBlas`、CUDA/HIP BLAS wrapper、dtype/device guard 和 Inductor lowering。若 ROCm 不支持 CUDA 已支持的模式，优先增加精确 capability guard 或 fallback 并给出明确错误，而不是广泛 skip。
