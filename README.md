# Optest Case Triage Skill

面向 PyTorch optest 单 case 深度分析的 Codex skill。它从 Excel 行或 pytest
nodeid 出发，完成问题复现、测试目的分析、官方修复检索、最小补丁、验证和
Markdown 记录；在用户明确要求时，还可以把已验证修改拆分成适合评审的
commit，并推送到个人 fork。

## 能力

- 从工作簿前三个 case 标识列或 pytest nodeid 定位测试。
- 兼容带或不带 `test/` 前缀的 pytest 路径。
- 结合测试代码确认测试目的，避免为了通过而曲解测试语义。
- 优先查找 PyTorch 官方 `main`、较新 release、目标 release、commit、PR
  和 issue，再检查内部 `upstream` 的较新开发分支。
- 在脏工作树中保留已有修改，实施范围明确的最小补丁。
- 验证精确 case 和受共享逻辑影响的邻近 case。
- 生成包含错误、根因、详细修改和验证结果的 Markdown 分析记录。
- 按根因拆分 commit，精确暂存，并限制 feature branch 只推送到 `origin`。

## 仓库结构

```text
optest-case-triage/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── commit_workflow.md
│   └── official_pytorch_skills.md
└── scripts/
    └── find_case_in_xlsx.py
```

`SKILL.md` 是主流程。只有用户明确要求提交或推送时，agent 才会读取
`references/commit_workflow.md`。

## 安装

克隆仓库：

```bash
git clone https://github.com/Zyq-gg/optest-case-triage-skill.git
```

安装工作簿查询脚本依赖：

```bash
python3 -m pip install -r optest-case-triage-skill/requirements.txt
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

工作 PyTorch 仓库应配置以下 remote：

| Remote | 用途 |
| --- | --- |
| `origin` | 个人 fork，用于开发分支、commit，以及明确要求后的 push |
| `upstream` | 内部主仓，用于同步目标分支和比较较新内部开发分支 |
| `official` | 官方 PyTorch，用于查找 `main`、release、commit、PR 和 issue |

例如本地开发分支为 `2.9.1-dev-xxx` 时，通常以
`upstream/2.9.1-dev` 为目标基线；官方版本覆盖则对应
`official/release/2.9`。

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
- 通过工作 PyTorch 仓库 `official/main` 直接读取 skill 的命令。

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

## 工作簿查询脚本

```bash
python3 optest-case-triage/scripts/find_case_in_xlsx.py \
  --xlsx /path/to/result.xlsx \
  --op-name test_name
```

同时提供 `--py-name`、`--class-name`、`--exact` 和 `--json` 选项。

## 环境说明

skill 当前包含该工作区常用环境：

```bash
source /home/tmp/python_and_sh/env-old.sh
```

用户明确指定工作仓库或环境时，以用户输入为准。运行测试前应确认实际导入的
`torch` 路径；如果环境从 `/usr/local/lib/python3.10/site-packages/torch`
导入 runtime，可以同步最小修改用于验证，但该安装目录副本不能进入源码
commit。

## 校验

使用 Codex 内置 `skill-creator` 校验器检查 skill 结构：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" \
  optest-case-triage
```
