# 可移植环境准备

每次开始 optest case 或 PyTorch 使用问题分析都要完整阅读本文。路径和工具必须从当前环境解析，不得假设最初开发 skill 的容器仍然存在。

## 目录

- [定位 skill 目录](#定位-skill-目录)
- [定位工作仓库](#定位工作仓库)
- [区分三类仓库](#区分三类仓库)
- [保护 dirty 工作区并使用 linked worktree](#保护-dirty-工作区并使用-linked-worktree)
- [确认 Python 与 PyTorch](#确认-python-与-pytorch)
- [定位工作簿与输出](#定位工作簿与输出)
- [映射 Git remote](#映射-git-remote)
- [处理编译与 runtime 源码验证](#处理编译与-runtime-源码验证)

## 定位 skill 目录

将 `<skill-dir>` 解析为当前所加载 `SKILL.md` 的所在目录。以下配套文件均相对于该目录：

```text
<skill-dir>/requirements.txt
<skill-dir>/scripts/find_case_in_xlsx.py
<skill-dir>/scripts/backfill_triage_csv.py
<skill-dir>/scripts/collect_pytorch_env.py
<skill-dir>/scripts/verify_runtime_sync.py
<skill-dir>/references/portable_setup.md
<skill-dir>/references/official_pytorch_skills.md
<skill-dir>/references/commit_workflow.md
<skill-dir>/references/csv_report_backfill.md
<skill-dir>/references/markdown_report.md
<skill-dir>/references/problem_triage.md
<skill-dir>/references/problem_report.md
```

不要通过硬编码 clone 路径反推 skill 位置。skill 可能通过符号链接安装、复制到 skills 目录，或直接从 clone 加载。

读取工作簿前检查依赖：

```bash
python3 -c "import openpyxl"
```

缺少依赖时报告下列安装命令，但未经用户允许不要安装：

```bash
python3 -m pip install -r <skill-dir>/requirements.txt
```

## 定位工作仓库

优先使用用户明确指定的编译仓和代码记录仓 PyTorch checkout。用户只指定一个 checkout 时，先确认它是否同时承担两个角色；未指定时，只有下列检查全部成功才可把某个当前目录作为候选，并仍需明确它承担的角色：

```bash
git rev-parse --show-toplevel
test -d torch
test -d test
test -f torch/version.py
```

否则不能猜测主机专用位置。Optest/pytest 模式需要源码时应向用户取得对应 checkout；使用问题明确属于配置、环境、用户项目或第三方且无需 PyTorch 源码时，将 PyTorch 编译仓和代码记录仓记为 `未使用/不适用`，不要为了填表阻塞诊断。

以 Git 顶层目录为基准解析仓库内测试路径。接受 `test/dynamo/test_x.py` 和 `dynamo/test_x.py`；后者通常表示命令从 `<repo>/test` 运行。

## 区分三类仓库

实际任务可能把构建、代码记录和安装验证分开。需要检查或修改 PyTorch 源码时，必须在开始测试前明确三类仓库；它们可以是同一个路径，但不能因为路径相同就省略角色记录。一般使用问题不涉及 PyTorch 源码时，允许编译仓和代码记录仓为 `未使用/不适用`，安装验证仓仍由实际 runtime 确认。

| 角色 | 定义 | 允许的修改和用途 | 提交边界 |
| --- | --- | --- | --- |
| 编译仓 | 只用于必须编译的 PyTorch C/C++、binding 或生成源码的临时镜像和既有构建产物，例如 `/workspace/pytorch-compile`。 | 默认保持不改。只有修改必须编译才能生效的文件时，才可同步代码记录仓中的相同源码 patch，并仅作记录和源码/static validation；test 文件和无需编译的 Python 文件禁止同步到这里。本 skill 不执行任何 PyTorch 源码编译。 | 临时源码镜像、既有 build 目录和生成文件不提交；若该路径同时被指定为代码记录仓，仍按逻辑角色隔离 test/runtime/build 边界。 |
| 代码记录仓 | 用于读取 test、保存所有 PyTorch 代码修改、创建 commit 和 push 的 checkout，例如 `/workspace/pytorch-code`。 | 所有 case 的源码和 test 修改都必须在此记录；pytest 使用这里的 test 代码；这里是提交建议、Git 状态、commit hash 和 MR/PR 边界的唯一权威来源。 | 只有该仓库中的目标 patch 才能进入 stage、commit 和 push；不得把编译仓或安装验证仓的镜像改动直接当作提交内容。 |
| 安装验证仓 | 由实际运行的 `torch.__file__` 动态解析出的已安装 torch 包目录，可能位于 `/usr`、virtualenv 或其他 site-packages。 | pytest 必须加载这里的 runtime。无需编译的 Python runtime 修改从代码记录仓同步到这里验证；本 skill 不生成或同步新的 PyTorch 二进制产物。test 文件不放入这里。 | 永远只作 validation-only；不得 stage、commit、push，也不得把其路径误写成代码记录仓源码路径。 |

默认角色映射：

```text
编译仓：<compile checkout>
代码记录仓：<code-record checkout>
安装验证仓：<Path(torch.__file__).resolve().parent>
```

如果用户只提供一个 PyTorch 路径，先询问或验证它是否同时承担编译仓和代码记录仓；如果用户明确说明它们相同，可以记录“编译仓 = 代码记录仓”。不能猜测另一个 checkout，也不能把安装验证仓通过固定 `/usr` 路径猜出来。

开始运行前记录每个角色的绝对路径、当前 branch/HEAD、dirty 状态，以及三者是否为同一份 checkout。编译仓存在未提交改动时，先区分它是用户已有改动、为当前 case 临时应用的 patch，还是 build 生成物；不得覆盖或清理用户改动。

三类仓库之间的同步规则：

1. 代码记录仓中的 patch 是逻辑和提交的源头；每个 applied diff 都从该仓库的 Git 生成。
2. pytest 的 test 源码始终来自代码记录仓；test-only patch 不同步到编译仓或安装验证仓。
3. 无需编译的 Python runtime patch 从代码记录仓直接同步到安装验证仓；不得为此修改编译仓。
4. 只有必须重新编译才能生效的源码 patch 才同步到编译仓，并且只作记录和源码/static validation。本 skill 不运行 `ninja`、`cmake --build`、`setup.py` 或等价的 PyTorch 源码构建命令，也不把既有 build 产物误写为当前 patch 的验证结果。
5. pytest 必须加载安装验证仓中的 `torch`。编译仓或安装验证仓中的验证副本与代码记录仓不一致时，不能宣称“修复后通过”；应标为“验证副本不一致”，先同步或说明差异。

按修改类型使用以下决策表，不得混用：

| 修改类型 | 代码记录仓 | 编译仓 | 安装验证仓 | 默认验证 |
| --- | --- | --- | --- | --- |
| test-only | 修改并作为 pytest test 来源 | 不改 | runtime 保持原状 | 从代码记录仓运行 test，确认导入安装验证仓 |
| 无需编译的 Python runtime | 修改并保存 diff | 不改 | 同步同一 Python 文件 | 从代码记录仓运行 test，确认导入安装验证仓 |
| 必须编译的源码 | 修改并保存 diff | 同步相同源码 patch，仅作记录/static validation | 不生成或同步新产物 | 明确记录按规则未编译、新二进制 runtime 验证未完成及残余风险 |

确认编译仓和代码记录仓：

```bash
git -C <compile-repo> rev-parse --show-toplevel
git -C <compile-repo> status --short --branch
git -C <compile-repo> rev-parse HEAD
git -C <code-record-repo> rev-parse --show-toplevel
git -C <code-record-repo> status --short --branch
git -C <code-record-repo> rev-parse HEAD
```

## 保护 dirty 工作区并使用 linked worktree

代码记录仓存在用户未提交修改，且切换目标分支可能覆盖、冲突或混入其他任务时，不要 stash、清理或强行 checkout。先确认已有 worktree、目标基线和开发分支是否存在：

```bash
git -C <code-record-repo> status --short --branch
git -C <code-record-repo> worktree list --porcelain
git -C <code-record-repo> rev-parse <internal-remote>/<target-branch>
git -C <code-record-repo> branch --list <dev-branch>
```

开发分支和目标路径均未占用时，可从精确基线创建 linked worktree：

```bash
git -C <code-record-repo> worktree add \
  -b <dev-branch> \
  <linked-worktree-path> \
  <internal-remote>/<target-branch>
```

linked worktree 与原路径共享同一个 Git object/ref 仓库，但有独立 checkout 和工作树。将它记录为“本问题代码记录 worktree”，同时记录原代码记录工作区及其 dirty 文件保持未动。后续 diff、stage、commit、push 都从本问题 worktree 执行；不能把新路径误写成另一个无关 clone。分支或路径已存在时先检查并复用安全的现有 worktree，不删除、强制重建或重置。

## 确认 Python 与 PyTorch

使用用户提供的环境激活命令。若未提供，保留并记录当前 shell 环境，不 source 猜测的脚本。

pytest 前执行：

```bash
command -v python
cd <code-record-repo>/test
python -c "import sys, torch; print(sys.executable); print(torch.__version__); print(torch.__file__)"
python -m pytest --version
```

`torch.__file__` 决定 pytest 实际导入的 runtime 代码，也就是安装验证仓。权威测试优先用 `python -c 'import torch, pytest; ...; pytest.main(...)'` 在 pytest 收集前导入并打印 `torch`，确保测试进程复用该安装 runtime。不得假设 Python 版本、virtualenv 布局或 site-packages 前缀。若它解析到代码记录仓、编译仓或非预期 editable package，先修正工作目录、`PYTHONPATH` 或安装状态；在 pytest 确认加载安装验证仓前不得继续权威验证。

## 定位工作簿与输出

使用用户提供的工作簿路径。若只给 basename 或行号，在当前任务目录查找唯一匹配的 `.xlsx`；存在多个候选时询问用户。

默认在工作簿旁创建同 basename 的 `.md`。例如 `/data/run.xlsx` 对应 `/data/run.md`。没有工作簿时，使用用户指定的输出路径，或在当前任务目录创建含义清晰的文件。

不得把输出默认到某台机器专用目录。

## 映射 Git remote

`origin`、`upstream`、`official` 是 PyTorch 代码记录仓的逻辑角色，不保证就是实际 remote 名。fetch 前先检查：

```bash
git -C <repo> remote -v
git -C <repo> branch -vv
```

推荐角色映射：

| 逻辑角色 | 常见名称 | 用途 |
| --- | --- | --- |
| 用户 fork | `origin` | 工作分支，以及用户明确要求的 push |
| 内部主线 | `upstream` | 目标分支同步和内部版本对比 |
| PyTorch GitHub | `official` | 官方 main、release、commit、PR、issue 和 skill |

名称不同时按 URL 或用户说明映射。只 fetch 已存在的 remote。未经用户明确要求，不新增、重命名或重写 remote。

若缺少 official remote，使用 `official_pytorch_skills.md` 的内置指导和 GitHub 链接检索官方修复。文档要注明无法进行本地官方分支包含关系检查，但不能因此阻止整个分析流程。

## 处理编译与 runtime 源码验证

测试源码和 runtime 的来源必须分别记录：测试只从代码记录仓读取，Python runtime 只从安装验证仓加载。不要使用编译仓的 test，不要让仓库根目录源码包或 editable install 静默替代安装验证仓。

始终动态解析安装验证仓：

```bash
python -c "from pathlib import Path; import torch; print(Path(torch.__file__).resolve().parent)"
```

无需编译的 Python runtime 文件按“代码记录仓 → 安装验证仓”同步，编译仓保持不动。必须编译的源码按“代码记录仓 → 编译仓”同步后仅作记录和源码/static validation。本 skill 不运行 `ninja`、`cmake --build`、`setup.py` 或等价命令编译 PyTorch，也不生成或同步新的二进制产物。报告应写明这是既定验证边界，并准确记录尚未覆盖的新二进制 runtime 行为；不要把既有安装仓或 build 产物的结果归因于未编译 patch。

分别记录每个验证副本的文件、基线和命令。安装验证仓中经验证有效的修改默认不回退，保留给用户后续复测；如果用户要求清理或切换版本，必须先记录当前副本状态再操作。绝不 stage 或 commit 编译仓临时 patch/build 产物、安装验证仓或工作仓库之外的文件。不得硬编码安装前缀、Python 版本或包管理器布局。

修改安装验证仓前，记录目标文件路径、原始 hash 和来源版本；同步后对每个 runtime 文件做字节一致性检查：

```bash
sha256sum <installed-runtime-file>

python3 <skill-dir>/scripts/verify_runtime_sync.py \
  --source <code-record-file> \
  --runtime <installed-runtime-file>
```

脚本退出码 `0` 表示两份文件字节一致，`1` 表示内容不一致，`2` 表示文件无法读取。只有一致时才能把安装环境的结果归因于代码记录仓 patch；若构建或安装过程理应产生不同文件，改用聚焦 diff 证明逻辑等价，并在报告中解释差异，不能伪造 hash 一致。
