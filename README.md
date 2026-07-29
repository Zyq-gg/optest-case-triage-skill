# Optest Case Triage Skill

面向 PyTorch optest 单 case 深度分析的 Codex skill。它从 Excel 行或 pytest
nodeid 出发，完成问题复现、测试目的分析、官方修复检索、最小补丁、验证和
Markdown 记录；在用户明确要求时，还可以把已验证修改拆分成适合评审的
commit，并推送到个人 fork。它也可在 triage 完成后，以 Markdown 为准、结合
位置不固定的 CSV 辅助列，安全回填 `测试目的`、`解决方案`、`最终状态`、
`遗留原因`。

## 能力

- 从工作簿前三个 case 标识列或 pytest nodeid 定位测试。
- 兼容带或不带 `test/` 前缀的 pytest 路径。
- 结合测试代码确认测试目的，避免为了通过而曲解测试语义。
- 优先查找 PyTorch 官方 `main`、较新 release、目标 release、commit、PR
  和 issue，再检查内部 `upstream` 的较新开发分支。
- 在脏工作树中保留已有修改，实施范围明确的最小补丁。
- 验证精确 case 和受共享逻辑影响的邻近 case。
- 生成包含错误、根因、详细修改和验证结果的 Markdown 分析记录。
- 将完成的 Markdown 分析汇总到 CSV 四个报告列，同时保持其它列、行顺序、
  UTF-8 BOM 和逻辑行数不变。
- 按根因拆分 commit，精确暂存，并限制 feature branch 只推送到 `origin`。

## 仓库结构

```text
optest-case-triage/
├── SKILL.md
├── requirements.txt
├── agents/
│   └── openai.yaml
├── references/
│   ├── commit_workflow.md
│   ├── csv_report_backfill.md
│   ├── official_pytorch_skills.md
│   └── portable_setup.md
├── scripts/
│   ├── backfill_triage_csv.py
│   └── find_case_in_xlsx.py
└── tests/
    └── test_backfill_triage_csv.py
```

`SKILL.md` 是主流程。只有用户明确要求提交或推送时，agent 才会读取
`references/commit_workflow.md`。运行所需的依赖声明、环境发现规则、官方
PyTorch skill 路由和辅助脚本都包含在这个目录中，复制或链接该目录即可使用。

## 安装

克隆仓库：

```bash
git clone https://github.com/Zyq-gg/optest-case-triage-skill.git
```

安装工作簿查询脚本依赖：

```bash
python3 -m pip install -r optest-case-triage-skill/optest-case-triage/requirements.txt
```

将 skill 目录链接到 Codex skills 目录：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -s "$(pwd)/optest-case-triage-skill/optest-case-triage" \
  "${CODEX_HOME:-$HOME/.codex}/skills/optest-case-triage"
```

也可以直接复制：

```bash
cp -a optest-case-triage-skill/optest-case-triage \
  "${CODEX_HOME:-$HOME/.codex}/skills/"
```

## PyTorch Remote 约定

skill 按逻辑角色识别 PyTorch remote，下面是推荐名称，但不要求 remote 必须
同名，也不会为了运行 skill 自动改写 remote：

| Remote | 用途 |
| --- | --- |
| `origin` | 个人 fork，用于开发分支、commit，以及明确要求后的 push |
| `upstream` | 内部主仓，用于同步目标分支和比较较新内部开发分支 |
| `official` | 官方 PyTorch，用于查找 `main`、release、commit、PR 和 issue |

例如本地开发分支为 `2.9.1-dev-xxx` 时，通常以
`upstream/2.9.1-dev` 为目标基线；官方版本覆盖则对应
`official/release/2.9`。缺少 `official` remote 时，仍可使用仓库内置的官方
诊断路由；有网络时再通过 GitHub 固定链接或实时链接刷新资料。

## PyTorch 官方 Skills 融合

本仓库分析并路由了 PyTorch 官方 `.claude/skills` 中的全部 16 个 skill。
直接融合的重点是 PT2 编译问题诊断、repro 最小化、AOTI、distributed、CUDA
大索引和提交前审查；ATen dispatch、uint、MPS、文档、类型检查和 CI metrics
等专门能力保留为条件链接。

完整评估和路由见
[`official_pytorch_skills.md`](optest-case-triage/references/official_pytorch_skills.md)。
其中同时保存：

- 指向官方 `main` 的实时链接，用于获取最新规则；
- 指向分析基准 commit 的固定链接，用于复现当时采用的规则；
- 通过工作 PyTorch 仓库可选的官方 remote 直接读取 skill 的命令；
- clone 后离线可用的核心诊断路由和检查项。

这里没有把 `pytorch/pytorch` 加成 Git submodule。Git submodule 不能只指向
`.claude/skills` 子目录，递归克隆会带入完整 PyTorch 仓库。使用 remote ref
和双链接能保持仓库轻量，也更容易随官方更新。

## 使用

可以从 Excel 中的一行开始：

```text
使用 $optest-case-triage，分析工作簿第 941 行的 test_sdpfa_cuda，复现、查找官方修复、验证并更新分析 Markdown。
```

也可以直接提供 pytest nodeid：

```text
使用 $optest-case-triage，分析 test/inductor/test_unbacked_symints.py::TestUnbackedSymintsCUDA::test_sdpfa_cuda。
```

只有明确提出 commit 或 push 时，skill 才进入提交阶段：

```text
根据根因把这些已验证修改分 commit 提交到当前开发分支，但暂时不要 push。
```

也可以单独执行 triage 后的 CSV 文档回填，不会重新进入 case 处理流程：

```text
根据现有 CSV 的相关辅助列并以分析 Markdown 为准，填写 CSV 的测试目的、解决方案、最终状态和遗留原因。
```

## 工作簿查询脚本

```bash
python3 optest-case-triage/scripts/find_case_in_xlsx.py \
  --xlsx /path/to/result.xlsx \
  --op-name test_name
```

同时提供 `--py-name`、`--class-name`、`--exact` 和 `--json` 选项。

CSV 回填先按
[`csv_report_backfill.md`](optest-case-triage/references/csv_report_backfill.md)
生成带行号和精确 case 身份的 JSON 更新计划，再执行：

```bash
python3 optest-case-triage/scripts/backfill_triage_csv.py \
  --csv /path/to/result.csv \
  --plan /path/to/updates.json \
  --dry-run
```

## 环境说明

skill 不绑定固定容器、目录、Python 版本或环境脚本。使用时优先采用用户给出的
工作仓库、工作簿和环境激活命令；没有明确输入时，只在当前目录通过以下特征
验证 PyTorch 仓库：

```text
.git/
torch/
test/
torch/version.py
```

运行测试前会记录 `sys.executable`、`torch.__version__` 和 `torch.__file__`。
如需验证安装包中的 runtime 修改，路径从 `torch.__file__` 动态解析，不假设
site-packages 布局，且验证副本不能进入源码 commit。完整规则见
[`portable_setup.md`](optest-case-triage/references/portable_setup.md)。

## 校验

clone 后可先验证辅助脚本及依赖：

```bash
python3 optest-case-triage/scripts/find_case_in_xlsx.py --help
python3 -m unittest discover -s optest-case-triage/tests -v
```

若当前 Codex 安装包含内置 `skill-creator`，还可以检查 skill 结构：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" \
  optest-case-triage
```
